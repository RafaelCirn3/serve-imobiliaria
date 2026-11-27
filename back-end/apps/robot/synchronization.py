"""MGA end-to-end sync, shared by the application command and integrations."""

from collections import Counter
from dataclasses import asdict
import hashlib
from io import BytesIO
import json
from pathlib import Path
from types import SimpleNamespace
from time import sleep
from urllib.parse import urlencode
from urllib.request import urlopen

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .drive import drive_service, scan_source
from .extraction.document import DocumentExtractor, ExtractionError, MAX_BYTES
from .extraction.service import inspect_table, stage_table, commit_unit, validation_issues
from .gallery import index_inventories, attach_images
from .models import DriveSource, TableImport, TableUnit
from .profile_defaults import COMPANIES
from .profiles import normalize
from .sources import DEFAULT_SOURCES
from .project_context import canonical_project, verified_context


class MGASynchronizer:
    def __init__(self, progress=None):
        self.progress = progress or (lambda message: None)
        self.service = None

    def inventory(self, checkpoint):
        self.service = drive_service()
        snapshot = {"started_at": timezone.now().isoformat(), "inventories": [], "errors": []}
        sources = [s for s in DriveSource.objects.filter(ativa=True) if "mga" in s.perfil.get("related_companies", [])]
        sources.sort(key=lambda s: s.pasta_id != DEFAULT_SOURCES[1][1])
        for source in sources:
            self.progress(f"Consultando fonte: {source.nome}")
            try:
                folders, files = scan_source(self.service, source, progress=self.progress)
                snapshot["inventories"].append({"source": {key:getattr(source,key) for key in ("pk","nome","pasta_id","perfil")},
                                                "folders":folders,"files":files})
                source.ultima_consulta_em = timezone.now()
                source.save(update_fields=["ultima_consulta_em"])
            except Exception as exc:
                snapshot["errors"].append({"source":source.pasta_id,"error":type(exc).__name__})
            checkpoint.parent.mkdir(parents=True, exist_ok=True)
            checkpoint.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2),encoding="utf-8")
        return snapshot

    def content(self, file):
        path = settings.BASE_DIR / f"reports/mga/input/{file['id']}.pdf"
        expected = file.get("md5_checksum")
        if path.exists() and expected and hashlib.md5(path.read_bytes()).hexdigest() == expected:
            return path.read_bytes()
        if (file.get("size") or 0) > MAX_BYTES:
            raise ExtractionError("Tabela excede 15 MB.")
        from googleapiclient.errors import HttpError
        from googleapiclient.http import MediaIoBaseDownload
        self.service = self.service or drive_service()
        buffer = BytesIO()
        downloader = MediaIoBaseDownload(buffer,self.service.files().get_media(fileId=file["id"],supportsAllDrives=True),chunksize=1024*1024)
        done = False
        try:
            while not done:
                _, done = downloader.next_chunk(num_retries=2)
                if buffer.tell() > MAX_BYTES:
                    raise ExtractionError("Tabela excede 15 MB.")
            content = buffer.getvalue()
        except HttpError:
            # Public source files can still be downloaded when the API media
            # endpoint temporarily rejects automated requests.
            if not expected:
                raise
            url = "https://drive.google.com/uc?" + urlencode({"export": "download", "id": file["id"]})
            with urlopen(url, timeout=30) as response:
                content = response.read(MAX_BYTES + 1)
            if len(content) > MAX_BYTES or not content.startswith(b"%PDF"):
                raise ExtractionError("Download público não retornou um PDF válido.")
        if expected and hashlib.md5(content).hexdigest() != expected:
            raise ExtractionError("Tabela mudou durante o download; tente novamente.")
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(content)
        return content

    def refresh(self, result, source_id, file_id):
        document = TableImport.objects.filter(drive_file_id=file_id, content_sha256=result["content_sha256"]).order_by("created_at").first()
        if not document:
            return stage_table(result,source_folder_id=source_id,drive_file_id=file_id)[0]
        def key(fields):
            return (normalize(canonical_project(fields.get("empreendimento",""))),
                    normalize(fields.get("torre","")),normalize(fields.get("unidade","")))
        fresh = {}
        for row in result["units"]:
            fresh.setdefault(key(row["fields"]),[]).append(row)
        with transaction.atomic():
            for unit in document.units.select_for_update():
                matches = fresh.get(key(unit.fields),[])
                if unit.reviewed or len(matches) != 1:
                    continue
                row = matches[0]
                if unit.fields == row["fields"] and unit.warnings == row["warnings"]:
                    continue
                previous = unit.fields
                from .extraction.service import property_payload, EDITABLE_FIELDS
                previous_payload = property_payload(unit)
                unit.fields,unit.warnings = row["fields"],row["warnings"]
                unit.evidence = {**unit.evidence,**{k:v for k,v in row.items() if k!="fields"},
                    "sync_history":[*unit.evidence.get("sync_history",[]),{"at":timezone.now().isoformat(),"parser":result["parser_version"],"before":previous}]}
                unit.save(update_fields=["fields","warnings","evidence"])
                if unit.imported_property_id:
                    from .models import ImportedUnitIdentity
                    property=unit.imported_property
                    payload=property_payload(unit)
                    for field in EDITABLE_FIELDS - {"valor"}:
                        value=payload.get(field)
                        current=getattr(property,field)
                        if value is not None and value!="" and (current in (None,"") or str(current)==str(previous_payload.get(field))):
                            setattr(property,field,value)
                    property.save()
                    stable=hashlib.sha256("|".join(normalize(getattr(property,field)) for field in
                        ("empreendimento","cidade","tipo","finalidade","torre","unidade")).encode()).hexdigest()
                    ImportedUnitIdentity.objects.filter(property=property).update(key=stable)
            document.extraction = {**document.extraction,"last_sync":{"at":timezone.now().isoformat(),"parser":result["parser_version"],"context":result["context"]}}
            document.save(update_fields=["extraction"])
        return document

    def run(self, snapshot, output, *, apply=False):
        inventories = [(SimpleNamespace(**row["source"]),row["folders"],row["files"]) for row in snapshot["inventories"]]
        report={"started_at":timezone.now().isoformat(),"applied":apply,"source_errors":snapshot.get("errors",[]),
                "documents":[],"duplicates":[],"units":[],"errors":[],"created":0,"existing":0,"pending":0,
                "published":0,"publication_pending":0}
        if apply:
            report["indexed_images"] = index_inventories(inventories)
        items=[]
        for source,folders,files in inventories:
            for file in files:
                classification,identity=file.get("classification",{}),file.get("project_identity",{})
                if classification.get("categoria")=="tabela_precos" and not classification.get("excluido") and (source.pasta_id==DEFAULT_SOURCES[1][1] or "mga" in identity.get("companies",[])):
                    items.append((source,file))
        extractor=DocumentExtractor(settings.BASE_DIR/"reports/mga/cache",self.progress)
        seen={}
        project_facts={}
        names={company.key:company.name for company in COMPANIES}
        for index,(source,file) in enumerate(items,1):
            self.progress(f"Tabela {index}/{len(items)}: {file['name']}")
            try:
                content=self.content(file)
                identity=file.get("project_identity",{})
                project=canonical_project(identity.get("name",""))
                fingerprint=(hashlib.sha256(content).hexdigest(),normalize(project))
                if fingerprint in seen:
                    report["duplicates"].append({"file_id":file["id"],"same_as":seen[fingerprint]})
                    continue
                seen[fingerprint]=file["id"]
                context={"empreendimento":project} if project else {}
                context.update(verified_context(project))
                shared=project_facts.get(normalize(project),{})
                for key,value in shared.get("fields",{}).items():
                    context.setdefault(key,value)
                if identity.get("companies"):
                    context["construtora"]=" / ".join(names[k] for k in identity["companies"] if k in names)
                # Resolve known neighborhoods without making city guesses for unknown projects.
                if normalize(project)=="elevare":
                    context.update(cidade="João Pessoa",natureza_area="total")
                result=inspect_table(content,file["name"],context,extractor=extractor)
                if shared:
                    for row in result["units"]:
                        row["raw"]["project_context_source"]=shared["file_id"]
                if project:
                    facts={}
                    for key in ("endereco","previsao_entrega","registro_incorporacao"):
                        values={row["fields"].get(key) for row in result["units"] if row["fields"].get(key)}
                        if len(values)==1 and key=="endereco":
                            facts[key]=values.pop()
                    if facts:
                        project_facts[normalize(project)]={"fields":facts,"file_id":file["id"]}
                report["documents"].append({"file_id":file["id"],"source_id":source.pasta_id,"filename":file["name"],"units":len(result["units"]),"project":project})
                if apply:
                    document=self.refresh(result,source.pasta_id,file["id"])
                    for unit in document.units.order_by("index"):
                        row={"candidate_id":unit.pk,"project":unit.fields.get("empreendimento"),"unit":unit.fields.get("unidade")}
                        try:
                            property,created=commit_unit(unit.pk,with_images=False)
                            report["created" if created else "existing"]+=1
                            row.update(property_id=property.pk,status=property.status)
                            row["gallery"]=attach_images(unit.pk,progress=self.progress)
                            from .publication import MGAPublicationPolicy
                            row["publication"] = MGAPublicationPolicy().apply(property.pk)
                            row["status"] = row["publication"]["status"]
                            if row["publication"].get("published"):
                                report["published"] += 1
                            elif row["status"] == "rascunho":
                                report["publication_pending"] += 1
                        except ValidationError as exc:
                            report["pending"]+=1
                            row["issues"]=exc.detail
                        except Exception as exc:
                            row["gallery_error"]=type(exc).__name__
                            report["errors"].append({"candidate_id":unit.pk,"error":type(exc).__name__})
                        report["units"].append(row)
                        self.checkpoint(output,report)
                        self.progress(f"Unidade {unit.pk}: {row.get('status','pendente')}, galeria {row.get('gallery',{}).get('total',0)} fotos")
            except Exception as exc:
                report["errors"].append({"file_id":file["id"],"error":type(exc).__name__})
                self.progress(f"Falha nesta tabela: {type(exc).__name__}")
            self.checkpoint(output,report)
        report["finished_at"]=timezone.now().isoformat()
        self.checkpoint(output,report)
        return report

    @staticmethod
    def checkpoint(output,report):
        output.parent.mkdir(parents=True,exist_ok=True)
        temporary=output.with_suffix(output.suffix+".tmp")
        temporary.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
        for attempt in range(6):
            try:
                temporary.replace(output)
                break
            except PermissionError:
                if attempt == 5:
                    raise
                sleep(0.1 * (attempt + 1))
