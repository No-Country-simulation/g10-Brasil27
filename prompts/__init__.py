"""
MediFlow - Pacote de Prompts Clínicos (Classificação, Extração e OCR Multimodal)
"""

from prompts.classificacao import PROMPT_CLASSIFICACAO
from prompts.extracao import PROMPT_EXTRACAO
from prompts.extracao_clinica import (
    PROMPT_OCR_MULTIMODAL,
    SYSTEM_PROMPT_MEDIFLOW,
    ResultadoExtracaoLLM,
    montar_prompt_extracao_texto,
)

__all__ = [
    "PROMPT_CLASSIFICACAO",
    "PROMPT_EXTRACAO",
    "PROMPT_OCR_MULTIMODAL",
    "SYSTEM_PROMPT_MEDIFLOW",
    "ResultadoExtracaoLLM",
    "montar_prompt_extracao_texto",
]
