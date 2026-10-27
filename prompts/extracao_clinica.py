"""
MediFlow - Prompts Unificados de Classificação, Visão Multimodal e Extração Clínica
Hackathon ONE G10 - Grupo 10: MediFlow

Responsáveis: Guilherme & Ingrid (Apoio Técnico IA / Multimodal)
Mapeamento: prompts/extracao_clinica.py
"""

from pydantic import BaseModel, Field
from contratos.modelos import ClassificacaoDocumento, DadosExtraidos
from prompts.classificacao import PROMPT_CLASSIFICACAO
from prompts.extracao import PROMPT_EXTRACAO


class ResultadoExtracaoLLM(BaseModel):
    """
    Contrato intermediário para Structured Outputs do Google Gemini (response_schema),
    unificando a classificação documental e as entidades clínicas extraídas em uma única chamada.
    """
    classificacao: ClassificacaoDocumento = Field(
        ...,
        description="Classificação da categoria do documento, especialidade, prioridade e score de confiança."
    )
    dados_extraidos: DadosExtraidos = Field(
        ...,
        description="Entidades clínicas extraídas do documento (paciente, médico/CRM, exame, diagnóstico, CID-10, medicamentos)."
    )
    texto_transcrito_ocr: str = Field(
        default="",
        description="Transcrição textual fiel do documento caso a entrada seja imagem ou PDF digitalizado."
    )


SYSTEM_PROMPT_MEDIFLOW = (
    "Você é o agente clínico autônomo MediFlow, especialista em auditoria médica, "
    "triagem hospitalar, NLP clínico e visão computacional multimodal.\n\n"
    "Sua tarefa é analisar documentos clínicos e administrativos (textos, PDFs digitais/digitalizados "
    "ou fotos de receitas/laudos) com rigor hospitalar absoluto.\n\n"
    f"### 1. DIRETRIZES DE CLASSIFICAÇÃO\n{PROMPT_CLASSIFICACAO}\n\n"
    f"### 2. DIRETRIZES DE EXTRAÇÃO CLÍNICA\n{PROMPT_EXTRACAO}\n"
)


PROMPT_OCR_MULTIMODAL = """Analise visualmente este documento clínico (imagem ou página de PDF digitalizado).
1. Transcreva todo o conteúdo textual visível no campo `texto_transcrito_ocr`, sinalizando com `[ilegível]` ou `[rasurado]` qualquer trecho borrado ou manuscrito incompreensível.
2. Execute a classificação clínica e a extração estruturada de todas as entidades seguindo rigorosamente o schema JSON definido."""


def montar_prompt_extracao_texto(documento_texto: str, canal_origem: str = "Pronto_Socorro") -> str:
    """
    Monta o prompt de usuário para análise de documento clínico textual ou pós-OCR.
    """
    return (
        f"Canal de Origem Hospitalar: {canal_origem}\n\n"
        f"--- INÍCIO DO DOCUMENTO CLÍNICO ---\n"
        f"{documento_texto}\n"
        f"--- FIM DO DOCUMENTO CLÍNICO ---\n\n"
        "Extraia os dados clínicos estruturados e classifique o documento conforme o contrato JSON."
    )
