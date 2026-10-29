"""
MediFlow - Prompt de Classificação Documental Clínica
Hackathon ONE G10 - Grupo 10: MediFlow

Responsáveis: Guilherme & Ingrid
Mapeamento: prompts/classificacao.py
"""

PROMPT_CLASSIFICACAO = """Classifique o documento clínico recebido em uma das categorias oficiais do MediFlow:
- "Receituário Médico"
- "Laudo de Exame de Imagem"
- "Laudo de Exame Laboratorial"
- "Guia de Solicitação de Procedimento"
- "Relatório de Alta/Internação"
- "Atestado Médico"
- "Documento Não Identificado / Ilegível"

Determine também:
1. `especialidade`: Especialidade médica associada ao documento (ex.: "Radiologia / Pneumologia", "Hematologia / Clínica Médica", "Clínica Geral", "Cardiologia").
2. `nivel_prioridade`:
   - "Emergência" ou "Urgente": Achados críticos com risco imediato à vida (ex.: TEP Agudo, Tromboembolismo Pulmonar, Infarto/IAM, AVC, Sepse, Hemorragia, Dispneia súbita).
   - "Prioritário": Documentos com pendências críticas, prescrições de controle especial ou ambiguidade que exija revisão rápida.
   - "Rotina": Exames normais de controle ambulatorial, receitas simples legíveis, guias eletivas ou atestados.
3. `score_confianca_classificacao` (0.0 a 1.0):
   - 0.90 a 1.00: Documento completo, legível e consistente.
   - 0.60 a 0.74: Documento com dados parciais.
   - Abaixo de 0.60: Documento com trechos "[ilegível]", rasuras, carimbo borrado, ausência de CRM ou dosagem duvidosa.
"""
