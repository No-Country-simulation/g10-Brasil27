# Exemplos sintéticos para a demonstração MediFlow

**Todos os dados abaixo são fictícios.** Estes exemplos servem para testar o fluxo técnico, não para orientar atendimento clínico.

## 1. Rotina

```json
{
  "documento_id": "DOC-DEMO-ROTINA-001",
  "tipo_arquivo": "TEXTO",
  "documento_texto": "ATESTADO MÉDICO FICTÍCIO. Paciente: Joana Exemplo. O documento informa afastamento por um dia. Profissional: Dra. Marina Teste, CRM fictício não informado. Documento legível.",
  "canal_origem": "Ambulatorio"
}
```

Resultado esperado: classificar como atestado médico se as evidências forem suficientes; encaminhar ao destino administrativo definido pela equipe. Campos ausentes devem permanecer ausentes, sem inventar CRM.

## 2. Possível urgência

```json
{
  "documento_id": "DOC-DEMO-URGENTE-001",
  "tipo_arquivo": "TEXTO",
  "documento_texto": "LAUDO FICTÍCIO DE EXAME DE IMAGEM. O texto do laudo descreve um achado crítico e recomenda avaliação médica urgente. Paciente e profissional são identificados apenas como dados de demonstração.",
  "canal_origem": "Pronto_Socorro"
}
```

Resultado esperado: sinalizar o texto explícito de urgência e encaminhar conforme as regras definidas pela equipe. A demonstração não deve alegar que o modelo fez diagnóstico independente.

## 3. Ambiguidade / revisão humana

```json
{
  "documento_id": "DOC-DEMO-AMBIGUO-001",
  "tipo_arquivo": "TEXTO",
  "documento_texto": "Documento clínico parcialmente ilegível. Não é possível identificar com segurança o tipo de documento, o nome do paciente ou a solicitação.",
  "canal_origem": "Recepcao"
}
```

Resultado esperado: baixa confiança ou classificação indeterminada, registro das ambiguidades e encaminhamento para revisão humana.
