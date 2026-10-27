"""Cliente HTTP para o back-end do MediFlow.

O contrato do endpoint ainda deve ser confirmado com o integrante responsável pelo FastAPI.
"""
import os
import requests

DEFAULT_API_URL = os.getenv("MEDIFLOW_API_URL", "http://localhost:8000")
DEFAULT_TRIAGE_PATH = os.getenv("MEDIFLOW_TRIAGE_PATH", "/triagem")


def enviar_texto(documento_id: str, tipo_arquivo: str, documento_texto: str,
                 canal_origem: str = "Recepcao", api_url: str = DEFAULT_API_URL,
                 triage_path: str = DEFAULT_TRIAGE_PATH) -> dict:
    """Envia texto no formato de exemplo especificado no PDF do MediFlow."""
    endpoint = f"{api_url.rstrip('/')}/{triage_path.lstrip('/')}"
    payload = {
        "documento_id": documento_id,
        "tipo_arquivo": tipo_arquivo,
        "documento_texto": documento_texto,
        "canal_origem": canal_origem,
    }
    response = requests.post(endpoint, json=payload, timeout=90)
    response.raise_for_status()
    return response.json()
