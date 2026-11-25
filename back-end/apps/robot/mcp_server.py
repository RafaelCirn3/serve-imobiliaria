"""MCP stdio local: ferramentas usam a API autenticada da Serve."""

import base64
import os

import httpx
from mcp.server.fastmcp import FastMCP


def create_server():
    server = FastMCP("Serve — robô MGA")
    base_url = os.environ.get("SERVE_API_URL", "http://127.0.0.1:8000").rstrip("/")

    def request(method, path, **kwargs):
        token = os.environ.get("SERVE_API_TOKEN", "")
        if not token:
            raise ValueError("Configure SERVE_API_TOKEN com JWT de administrador.")
        if not base_url.startswith("https://") and not base_url.startswith(("http://127.0.0.1:", "http://localhost:")):
            raise ValueError("Use HTTPS para conectar a uma API remota.")
        with httpx.Client(timeout=180, follow_redirects=False) as client:
            response = client.request(method, base_url + path, headers={"Authorization": f"Bearer {token}"}, **kwargs)
        if response.status_code >= 400:
            # Nenhuma exceção do cliente HTTP contendo headers é exposta ao host.
            raise ValueError(f"API Serve retornou HTTP {response.status_code}. Confira os campos e permissões na API.")
        return response.json()

    @server.tool()
    def mga_extrair_tabela(nome: str, arquivo_base64: str, contexto: dict | None = None, salvar: bool = False) -> dict:
        """Extrai PDF/PNG/JPEG MGA. Por padrão só antecipa dados; salvar cria candidatos, nunca anúncios."""
        import json

        if len(arquivo_base64) > 21 * 1024 * 1024:
            raise ValueError("Arquivo maior que 15 MB.")
        content = base64.b64decode(arquivo_base64, validate=True)
        return request("POST", "/api/admin/robot/mga/extracoes/", files={"arquivo": (nome, content)},
                       data={"contexto": json.dumps(contexto or {}), "preview": str(not salvar).lower()})

    @server.tool()
    def mga_consultar_extracao(extracao_id: str) -> dict:
        """Consulta campos, evidências, pendências e imóveis associados a uma extração."""
        from uuid import UUID

        identifier = str(UUID(extracao_id))
        return request("GET", f"/api/admin/robot/mga/extracoes/{identifier}/")

    @server.tool()
    def mga_revisar_unidade(unidade_id: int, campos: dict, aprovar: bool = False) -> dict:
        """Registra correções e aprovação explícita de OCR ou campos ausentes."""
        return request("PATCH", f"/api/admin/robot/mga/unidades/{int(unidade_id)}/", json={"fields": campos, "approve": aprovar})

    @server.tool()
    def mga_importar_rascunho(unidade_id: int) -> dict:
        """Cria rascunho de unidade validada. Repetição não duplica nem altera imóvel existente."""
        return request("POST", f"/api/admin/robot/mga/unidades/{int(unidade_id)}/importar/")

    return server


if __name__ == "__main__":
    create_server().run(transport="stdio")
