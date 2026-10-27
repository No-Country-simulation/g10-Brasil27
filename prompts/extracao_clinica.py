"""
MediFlow - Prompts de Classificação, Visão Multimodal e Extração Clínica
Hackathon ONE G10 - Grupo 10: MediFlow

Responsáveis: Guilherme & Ingrid (Apoio Técnico IA / Multimodal)
Mapeamento: prompts/extracao_clinica.py
"""

from pydantic import BaseModel, Field
from contratos.modelos import ClassificacaoDocumento, DadosExtraidos


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


SYSTEM_PROMPT_MEDIFLOW = """Você é o agente clínico autônomo MediFlow, especialista em auditoria médica, triagem hospitalar, NLP clínico e visão computacional multimodal.

Sua tarefa é analisar documentos clínicos e administrativos (textos, PDFs digitais/digitalizados ou fotos de receitas/laudos) com rigor hospitalar absoluto:

1. CLASSIFICAÇÃO DOCUMENTAL (`classificacao`):
   - `tipo_documento`: Classifique estritamente em uma das categorias:
     * "Receituário Médico"
     * "Laudo de Exame de Imagem"
     * "Laudo de Exame Laboratorial"
     * "Guia de Solicitação de Procedimento"
     * "Relatório de Alta/Internação"
     * "Atestado Médico"
     * "Documento Não Identificado / Ilegível"
   - `especialidade`: Identifique a especialidade médica associada (ex.: "Radiologia / Pneumologia", "Hematologia / Clínica Médica", "Clínica Geral", "Cardiologia").
   - `nivel_prioridade`:
     * "Emergência" ou "Urgente": Achados críticos com risco de vida (ex.: TEP Agudo, Tromboembolismo Pulmonar, IAM, AVC, Sepse, Hemorragia, Dispneia súbita).
     * "Prioritário": Documentos com pendências críticas, prescrições de controle especial ou ambiguidade que exija revisão rápida.
     * "Rotina": Exames normais de controle ambulatorial, receitas simples legíveis, guias eletivas ou atestados.
   - `score_confianca_classificacao`:
     * Entre 0.90 e 1.00 para documentos claros, completos e legíveis.
     * Entre 0.60 e 0.74 para documentos com dados parciais (ex.: falta idade ou CID).
     * Abaixo de 0.60 (ex.: 0.35 a 0.55) quando houver trechos "[ilegível]", rasuras, carimbo borrado, ausência de CRM ou dosagem medicamentosa duvidosa.

2. EXTRAÇÃO DE ENTIDADES CLÍNICAS (`dados_extraidos`):
   - `paciente`: Extraia `nome` e `idade` (em anos inteiros, se constar). Nunca invente dados ausentes. Se o nome estiver truncado/ilegível, indique claramente.
   - `medico_solicitante`: Extraia `nome` e `crm` padronizado no formato `NUMERO-UF` (ex.: `145892-SP`, `98214-SP`). Se o CRM estiver ilegível ou ausente, retorne `null`.
   - `exame_realizado`: Nome do exame de imagem ou laboratorial, se aplicável.
   - `diagnostico_principal`: Diagnóstico clínico principal ou conclusão do laudo.
   - `cid_sugerido`: Código CID-10 correspondente ao quadro clínico (ex.: `I26.9` para TEP Agudo, `Z01.7` para exame laboratorial de rotina). Se não for possível inferir com segurança em documento ilegível, retorne `null`.
   - `medicamentos`: Lista de medicamentos prescritos (nome, dosagem, frequência, via de administração e duração) caso seja um Receituário Médico ou Relatório.
   - `observacoes_clinicas`: Resumo objetivo dos achados relevantes ou alertas sobre rasuras/ilegibilidade.

3. SEGURANÇA DO PACIENTE (HUMAN-IN-THE-LOOP):
   - Jamais adivinhe dosagens de medicamentos ou números de CRM borrados.
   - Preserve indicações de ilegibilidade para que o motor de regras retenha o documento na Fila de Revisão Humana.
"""


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
