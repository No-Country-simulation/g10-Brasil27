"""
MediFlow - Prompt de Extração Estruturada de Entidades Clínicas
Hackathon ONE G10 - Grupo 10: MediFlow

Responsáveis: Guilherme & Ingrid
Mapeamento: prompts/extracao.py
"""

PROMPT_EXTRACAO = """Extraia com precisão cirúrgica as entidades clínicas e administrativas do documento:
1. `paciente`:
   - `nome`: Nome completo do paciente (nunca invente dados ausentes; sinalize caso esteja truncado ou ilegível).
   - `idade`: Idade em anos inteiros, se constar no documento.
2. `medico_solicitante`:
   - `nome`: Nome do médico solicitante ou prescritor.
   - `crm`: Registro no formato padronizado `NUMERO-UF` (ex.: `145892-SP`, `98214-SP`). Se estiver ilegível ou ausente, retorne `null`.
3. `exame_realizado`: Nome do exame laboratorial ou de imagem, quando aplicável.
4. `diagnostico_principal`: Diagnóstico clínico principal ou conclusão do laudo.
5. `cid_sugerido`: Código CID-10 correspondente ao quadro clínico (ex.: `I26.9` para TEP Agudo, `Z01.7` para exame laboratorial de rotina). Em documento ilegível, retorne `null`.
6. `medicamentos`: Lista de medicamentos prescritos (`nome`, `dosagem`, `frequencia`, `via_administracao`, `duracao`). Jamais adivinhe dosagens borradas ou rasuradas.
7. `observacoes_clinicas`: Resumo objetivo dos achados relevantes ou alertas sobre rasuras/ilegibilidade para revisão humana (Human-in-the-Loop).
"""
