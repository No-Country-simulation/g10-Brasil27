"""
MediFlow - API REST (FastAPI)
Hackathon ONE G10 - Grupo 10: MediFlow

Mapeamento: api/main.py
Execução (a partir da raiz): python -m uvicorn api.main:app --reload
"""

import logging
import re
from functools import lru_cache

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse

from api.triagem import processar_triagem
from armazenamento.repositorio import (
    FalhaArmazenamento,
    ObjetoJaExiste,
    RepositorioDocumentos,
    criar_repositorio,
)
from contratos.modelos import DocumentoEntrada, TriagemResposta

load_dotenv()

logger = logging.getLogger("mediflow.api")

# O documento_id vira nome de objeto no bucket: "/" e ".." são proibidos.
PADRAO_DOCUMENTO_ID = re.compile(r"[A-Za-z0-9-]{1,64}")

app = FastAPI(title="MediFlow API", version="0.1.0")


@lru_cache(maxsize=1)
def obter_repositorio() -> RepositorioDocumentos:
    """Criado uma vez, no primeiro uso. Os testes o substituem com app.dependency_overrides."""
    return criar_repositorio()


@app.exception_handler(ObjetoJaExiste)
async def tratar_objeto_ja_existe(request, exc):
    return JSONResponse(
        status_code=409,
        content={"detail": "Documento com este documento_id já foi recebido."},
    )


@app.exception_handler(FalhaArmazenamento)
async def tratar_falha_armazenamento(request, exc):
    # A mensagem da exceção já é segura (sem credenciais nem OCIDs): vai para o log.
    logger.error("Falha de armazenamento: %s", exc)
    return JSONResponse(
        status_code=503,
        content={"detail": "Falha ao gravar o documento no armazenamento."},
    )


@app.get("/api/v1/saude")
def saude(repositorio: RepositorioDocumentos = Depends(obter_repositorio)):
    return {"status": "ok", "armazenamento": repositorio.nome}


@app.post("/api/v1/triagem", response_model=TriagemResposta)
def triagem(
    entrada: DocumentoEntrada,
    repositorio: RepositorioDocumentos = Depends(obter_repositorio),
):
    # Validações que deveriam estar no contrato (ver relatório). Rodam antes de qualquer gravação.
    if not PADRAO_DOCUMENTO_ID.fullmatch(entrada.documento_id):
        raise HTTPException(
            status_code=422,
            detail="documento_id inválido: use de 1 a 64 caracteres entre letras, números e hífen.",
        )
    tem_texto = bool(entrada.documento_texto and entrada.documento_texto.strip())
    tem_base64 = bool(entrada.documento_base64 and entrada.documento_base64.strip())
    if not (tem_texto or tem_base64):
        raise HTTPException(
            status_code=422,
            detail="Informe documento_texto (não vazio) ou documento_base64.",
        )

    return processar_triagem(entrada, repositorio)
