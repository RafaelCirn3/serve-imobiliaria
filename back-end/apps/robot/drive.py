"""Leitura completa e paginada das fontes de divulgação no Google Drive."""

import json
from time import sleep

from django.conf import settings

from .profiles import get_profile
from .mapping import annotate_inventory


FOLDER_MIME = "application/vnd.google-apps.folder"
DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.readonly"


class DriveAccessError(Exception):
    """Erro do Drive sem URL da requisição ou chave de API no texto."""


def execute(request):
    from googleapiclient.errors import HttpError

    for attempt in range(3):
        try:
            return request.execute()
        except HttpError as exc:
            if exc.resp.status in (429, 500, 502, 503, 504) and attempt < 2:
                sleep(2 ** attempt)
                continue
            raise DriveAccessError(
                f"Google Drive API retornou HTTP {exc.resp.status}. "
                "Confira a ativação da API, as restrições da chave e o acesso às pastas."
            ) from None


def drive_service():
    from google.auth import default
    from google.auth.exceptions import DefaultCredentialsError
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    if settings.GOOGLE_DRIVE_CREDENTIALS_JSON:
        info = json.loads(settings.GOOGLE_DRIVE_CREDENTIALS_JSON)
        credentials = service_account.Credentials.from_service_account_info(info, scopes=[DRIVE_SCOPE])
    elif settings.GOOGLE_DRIVE_CREDENTIALS_FILE:
        credentials = service_account.Credentials.from_service_account_file(
            settings.GOOGLE_DRIVE_CREDENTIALS_FILE, scopes=[DRIVE_SCOPE]
        )
    elif settings.GOOGLE_DRIVE_API_KEY:
        return build("drive", "v3", developerKey=settings.GOOGLE_DRIVE_API_KEY, cache_discovery=False)
    else:
        try:
            credentials, _ = default(scopes=[DRIVE_SCOPE])
        except DefaultCredentialsError as exc:
            raise RuntimeError(
                "Credenciais do Google Drive não configuradas. Defina "
                "GOOGLE_DRIVE_CREDENTIALS_FILE, GOOGLE_DRIVE_CREDENTIALS_JSON "
                "ou GOOGLE_DRIVE_API_KEY (somente pastas públicas) "
                "(ou configure Application Default Credentials)."
            ) from exc
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def scan_source(service, source):
    """Retorna pastas e arquivos sem omitir páginas nem atravessar atalhos."""
    profile = get_profile(source)
    project_depth = profile.depth if profile else 1
    api = service.files()
    root = execute(api.get(fileId=source.pasta_id, fields="id,name,mimeType,webViewLink", supportsAllDrives=True))
    if root["mimeType"] != FOLDER_MIME:
        raise ValueError(f"A fonte {source.nome} não é uma pasta do Drive.")

    folders = []
    files = []
    visited = set()
    stack = [(root, "", 0, None)]
    while stack:
        folder, parent_path, depth, project_id = stack.pop()
        folder_id = folder["id"]
        if folder_id in visited:
            continue
        visited.add(folder_id)
        path = f"{parent_path}/{folder['name']}" if parent_path else folder["name"]
        project_id = folder_id if depth == project_depth else project_id
        folders.append({
            "source_id": source.pk, "source_name": source.nome, "id": folder_id,
            "name": folder["name"], "path": path, "parent_id": folder.get("parent_id", ""),
            "depth": depth, "project_id": project_id or folder_id,
            "url": folder.get("webViewLink") or f"https://drive.google.com/drive/folders/{folder_id}",
        })
        children = []
        page_token = None
        while True:
            result = execute(api.list(
                q=f"'{folder_id}' in parents and trashed = false",
                fields="nextPageToken,files(id,name,mimeType,size,modifiedTime,webViewLink,description,md5Checksum,sha256Checksum,imageMediaMetadata(width,height))",
                pageSize=1000,
                pageToken=page_token,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            ))
            children.extend(result.get("files", []))
            page_token = result.get("nextPageToken")
            if not page_token:
                break
        for child in sorted(children, key=lambda item: (item["name"].casefold(), item["id"]), reverse=True):
            if child["mimeType"] == FOLDER_MIME:
                stack.append((child | {"parent_id": folder_id}, path, depth + 1, project_id))
            else:
                files.append({
                    "source_id": source.pk, "source_name": source.nome, "id": child["id"],
                    "name": child["name"], "folder_id": folder_id, "folder_path": path,
                    "project_id": project_id or folder_id, "mime_type": child["mimeType"],
                    "size": int(child["size"]) if child.get("size") else None,
                    "modified_time": child.get("modifiedTime", ""),
                    "description": child.get("description", ""),
                    "md5_checksum": child.get("md5Checksum", ""),
                    "sha256_checksum": child.get("sha256Checksum", ""),
                    "image_metadata": child.get("imageMediaMetadata", {}),
                    "url": child.get("webViewLink") or f"https://drive.google.com/file/d/{child['id']}/view",
                })
    if profile:
        annotate_inventory(source, folders, files)
    return folders, files
