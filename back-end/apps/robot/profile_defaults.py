"""Filtros por fonte transcritos da análise fornecida em 24/11/2026.

As empresas relacionadas a uma origem não são automaticamente responsáveis
por todos os seus empreendimentos. Os perfis são copiados ao banco pela migração.
"""

from .profiles import Company
from .sources import DEFAULT_SOURCES


COMPANIES = tuple(Company(key, name) for key, name in (
    ("alliance", "Alliance"), ("mga", "MGA Construções"),
    ("tropical", "Tropical"), ("brascon", "Brascon"),
    ("lavie", "Lavie Construtora"), ("space", "Space Incorporadora"),
    ("drx", "DRX"), ("icon", "Icon"), ("tf", "TF Construtora"),
    ("bauten", "Bauten"), ("holanda", "Holanda"), ("dion", "Dion"), ("setai", "Setai"),
))

GLOBAL_EXCLUSIONS = "feed;story;stories;reels;carrossel;card;criativos;logo;logomarca;logomarcas;branding;institucional;contrato;certidao;documentacao;registro de incorporacao;acompanhamento de obra;acompanhamento da obra;relatorio de obra;memorial;masterplan;planta tecnica;planta humanizada;plantas;planta baixa;video;videos;filme;filmes;renders animados"


def rule(folders="", keywords=""):
    return {"folders": folders.split(";") if folders else [], "keywords": keywords.split(";") if keywords else []}


def profile(index, origin, companies, prices, facade, leisure, indoors, *, project=None,
            depth=1, mixed=False, responsible=None, mode="projects", exclude="", notes=""):
    return {
        "code": ("BASE-01", "BASE-02")[index] if index < 2 else f"{index - 1:02}",
        "origin": origin, "related_companies": companies.split(";") if companies else [],
        "responsible_companies": (responsible if responsible is not None else companies).split(";") if (responsible if responsible is not None else companies) else [],
        "mixed": mixed, "confidence": "revisao" if index == 2 else "alta",
        "project_name": project, "project_depth": depth, "mode": mode,
        "categories": {key: value for key, value in zip(("tabela_precos", "fachada", "lazer", "internos"), (prices, facade, leisure, indoors)) if value is not None},
        "exclude": (GLOBAL_EXCLUSIONS + (";" + exclude if exclude else "")).split(";"),
        "notes": notes,
    }


PROFILES = (
    profile(0, "Empreendimentos / Alliance", "alliance",
        rule("tabelas comerciais", "tabela"), rule("", "fachada;externa"),
        rule("lazer", "lazer;piscina;academia;gourmet;kids;petplace;churrasqueiras"),
        rule("", "sala;living;cozinha;suite;quarto;decorado"),
        exclude="pecas redes sociais;fotos para fornecedores",
        notes="Associar PDFs de TABELAS COMERCIAIS por nome do empreendimento; revisar cópias de fornecedores."),
    profile(1, "Tabelas MGA", "mga",
        rule("tabela;tabelas", "tabela;tabela de vendas;tabela avulsos"),
        rule("fachada", "fachada;fachada diurna;fachada noite"),
        rule("areas comuns", "academia;piscina;wellness;gourmet;cinema;coworking"),
        rule("", "apartamento;sala;suite master;cozinha;decorado"), exclude="material de divulgacao;instagram"),
    profile(2, "ARC Space / Lavie / Space Inc.", "lavie;space",
        rule("materiais prioritarios/tabela", "tabela"), rule("", "fachada"),
        rule("", "business club;lounge;coworking"),
        rule("", "sala comercial;sala de reuniao;living;cozinha;modulo;podcast"),
        project="ARC Space", depth=0,
        notes="Relação Lavie/Space sujeita a confirmação. Tabela dezembro/2025 exige revisão. RENDERS e IMAGENS/IMAGENS são candidatos, não evidência de ambiente."),
    profile(3, "Material comercial DRX", "drx",
        rule("tabela", "tabela;tabela de precos;tabela zero"), rule("fachada", "fachada;fachada aerea"),
        rule("rooftop;academia;brinquedoteca", "piscina;salao de festas;snooker bar;coworking"),
        rule("unidade", "apartamento;sala;cozinha;decorado"), exclude="acompanhamento de obra;divulgacao",
        notes="Preservar tabelas BLACK DRX promocionais e convencionais separadamente."),
    profile(4, "Urban Prime", "", rule("", "tabela de novembro;tabela"),
        rule("", "fachada;entrada aproximada;vista aerea"), rule("", "academia;espaco gourmet;piscina;coworking"),
        rule("", "sala apt;apartamento;quarto"), project="Urban Prime", depth=0),
    profile(5, "Grupo Pirâmide", "dion;mga;setai", rule("tabelas", "tabela"),
        rule("", "fachada"), rule("", "piscina;academia;area gourmet;rooftop"),
        rule("", "apto decorado;apartamento decorado;sala;cozinha"), mixed=True, responsible="",
        notes="Origem comercial, não construtora. Mondo associado à MGA; demais atribuições exigem evidência por empreendimento."),
    profile(6, "MOSS / Icon", "icon", rule("tabela", "tabela"), rule("imagens/fachada", "fachada"),
        rule("imagens/cobertura/solario", "piscina;academia;gourmet"), rule("imagens/flats", "flat"),
        project="MOSS", depth=0, exclude="midias;subsolo;sumario descritivo",
        notes="TERREO exige nome específico do ambiente; não classificar todo térreo como lazer."),
    profile(7, "Compartilhado Tropical / Brascon / MGA", "tropical;brascon;mga",
        rule("tabela;tabelas por torre", "tabela;tabela de vendas"), rule("fachadas", "fachada"),
        rule("areas comuns;lazer", "piscina;gourmet;academia"),
        rule("interiores", "casa decorada;decorado;casa modelo;sala;suite;cozinha"), mixed=True, responsible="", exclude="kits",
        notes="Preservar torre/bloco/lojas. Priorizar fotos reais. Avulsos exigem associação individual. Não atribuir todos à Tropical."),
    profile(8, "TF Construtora", "tf", rule("", "tabela;tabela tf;tabela avulso"),
        rule("fachada", "fachada"), rule("lazer social;area de lazer;academia;cobertura lazer social", "piscina;solario"),
        rule("sala;cozinha;suite;quarto;wc;varanda", ""), depth=2, exclude="garagem",
        notes="Agrupar por empreendimento abaixo da etapa. Nomes genéricos dependem da pasta. HEIF permanece candidato; conversão não implementada."),
    profile(9, "Brascon / Imóveis avulsos", "brascon", rule("", "tabela avulsos"),
        rule("", "fachada"), rule("", "academia;brinquedoteca;piscina;gourmet;sauna;playground;splashup"),
        rule("", "sala 109;sala 601;sala 603;sala 605"), responsible="", mode="avulsos",
        notes="Brascon é origem; validar responsável por imóvel. IMG01 e similares exigem revisão visual."),
    profile(10, "Elevare / MGA / Tropical", "mga;tropical", rule("tabela", "tabela de vendas;tabela"),
        rule("", "fachada diurna;fachada noite;fachada aproximada"),
        rule("", "academia;churrasqueira gourmet;piscina;wine gourmet;cinema;garage band"),
        rule("", "sala apartamento;suite master apartamento"), project="Elevare", depth=0),
    profile(11, "Bauten", "bauten", rule("tabela;tabelas;tabela promocional", "tabela"),
        rule("fachadas;fachada", "fachada frontal;fachada nascente"),
        rule("areas comuns;ambientacoes", "piscina;gourmet;cobertura"),
        rule("unidades;apartamentos", "sala apt;cozinha apt;quarto"), exclude="ao corretor;publicacoes redes sociais",
        notes="Separar casas/apartamentos e promoções. MIME identifica PDF sem extensão. Áurea 100% vendido exige revisão de disponibilidade."),
    profile(12, "Externas finais", "", None, rule("", "externas"), None, None,
        depth=0, mode="complementary", notes="Somente mídia complementar. Externas são candidatas, não fachadas confirmadas. Associação manual obrigatória."),
    profile(13, "Tabela de avulsos", "", rule("", "tabela de avulsos"), None, None, None,
        depth=0, mode="commercial_only", notes="Somente extração comercial; não procurar imagens nem criar empreendimento automaticamente."),
    profile(14, "Holanda Gold Hotel Tambaú", "holanda", rule("", "tabela de precos;hgh tambau"), None,
        rule("areas comuns", "piscina;academia"), rule("apto final;aptos final;aptos 14 e 21", ""),
        project="Gold Hotel Tambaú", depth=0, notes="Preservar finais/tipologias no caminho original. Fachada precisa de análise adicional."),
    profile(15, "Holanda Gold Hotel Bessa", "holanda", rule("", "tabela de precos;hgh praia do bessa"),
        rule("", "fachada frontal"), rule("", "piscina;academia;restaurante;jardim interno"),
        rule("", "living;quarto;suite;apartamento"), project="Gold Hotel Bessa", depth=0,
        notes="Priorizar IMAGENS COMERCIAIS 01; RENDERS complementar. Cópias exigem deduplicação de conteúdo antes de publicação."),
)

# Pastas amplas orientam seleção/revisão, mas não comprovam a categoria sozinhas.
for index, paths in {
    0: ["fotos", "renders", "fotos reais"],
    1: ["imagens", "fotos"],
    2: ["imagens/imagens", "renders"],
    5: ["materiais"],
    6: ["imagens/terreo"],
    7: ["fotos reais", "imagens", "casa modelo"],
    15: ["imagens comerciais 01", "renders"],
}.items():
    PROFILES[index]["candidate_folders"] = paths
PROFILES[7]["priority_folders"] = ["fotos reais", "imagens"]
PROFILES[15]["priority_folders"] = ["imagens comerciais 01", "renders"]

DEFAULT_PROFILES = {source[1]: config for source, config in zip(DEFAULT_SOURCES, PROFILES, strict=True)}


def upgrade_profile(config):
    """Defaults V2 não sobrescrevem regras personalizadas persistidas no admin."""
    from .profiles import IMAGE_MIMES, ORGANIZATIONAL, TABLE_MIMES

    config.setdefault("rules_version", "2.0.0")
    config.setdefault("organizational_names", list(ORGANIZATIONAL))
    config.setdefault("thresholds", {"category": 80, "project": 80, "developer": 80})
    config.setdefault("company_roles", {key: "incorporadora" if key == "space" else "construtora" for key in config.get("related_companies", [])})
    config.setdefault("keyword_aliases", {"internos": ["cozinha", "sala", "quartos", "flat"]} if config["code"] == "10" else {})
    for category, rule in config.get("categories", {}).items():
        rule.setdefault("mime_types", list(TABLE_MIMES if category == "tabela_precos" else IMAGE_MIMES))
        rule.setdefault("enabled", True)
    config.setdefault("exclusion_exceptions", ["sala de video", "sala de podcast"] if config["code"] == "01" else [])
    phrases = {
        "sala de estar": "internos", "sala de jogos": "lazer", "sala de massagem": "lazer",
        "cozinha gourmet comum": "lazer", "cozinha privativa": "internos",
        "piscina coletiva": "lazer", "piscina privativa": "internos", "fachada frontal": "fachada",
    }
    # As expressões só se aplicam às categorias habilitadas no perfil.
    if config["code"] == "01":
        phrases.update({"sala comercial": "internos", "sala de reuniao": "internos", "sala de video": "internos",
                        "sala de podcast": "internos", "business club living": "lazer", "lounge cozinha": "lazer"})
    config.setdefault("semantic_phrases", {phrase: category for phrase, category in phrases.items() if category in config["categories"]})
    config.setdefault("canonical_projects", [{
        "key": "mga-tropical:elevare", "name": "Elevare", "aliases": ["MGA Elevare", "Cópia de Elevare"],
        "companies": ["mga", "tropical"], "related_companies": ["mga", "tropical"],
        "sources": ["BASE-02", "06", "09"], "confidence": "alta",
    }] if config["code"] in ("BASE-02", "06", "09") else [])
    aliases = {
        "materiais arian intermares": "Arian", "materiais mirai altiplano": "Mirai",
        "materiais mondo bessa": "Mondo", "materiais new wave home flat cabo branco": "New Wave",
        "materiais aqua manaira": "Aqua",
    } if config["code"] == "04" else {}
    config.setdefault("project_aliases", aliases)
    if config["code"] == "05":
        from .asset_reviews import ICON_MOSS_REVIEWS
        reviews = config.setdefault("visual_reviews", {})
        for file_id, review in ICON_MOSS_REVIEWS.items():
            reviews.setdefault(file_id, review)
        if "revista" not in config["exclude"]:
            config["exclude"].append("revista")
    if config["code"] == "04":
        aliases_by_category = config.setdefault("keyword_aliases", {})
        for category, words in {"fachada": ["imagem drone frontal"],
                                "lazer": ["spa", "lobby", "bar oval", "cinema"],
                                "internos": ["apto decorado"]}.items():
            configured_words = aliases_by_category.setdefault(category, [])
            for word in words:
                if word not in configured_words:
                    configured_words.append(word)
        config["project_aliases"].setdefault("materiais san. cabo branco", "SETAI Sandro Barros")
        entries = config.setdefault("canonical_projects", [])
        if not any(entry.get("key") == "setai:sandro-barros" for entry in entries):
            entries.append({"key": "setai:sandro-barros", "name": "SETAI Sandro Barros",
                            "aliases": ["Sandro Barros", "MATERIAIS SAN. CABO BRANCO"],
                            "companies": ["setai"], "confidence": "alta"})
    config.setdefault("central_tables", config["code"] in ("BASE-01", "02", "04"))
    return config


for config in PROFILES:
    upgrade_profile(config)
