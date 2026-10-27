# Integração da Fase 1 — Como rodar

**Branch:** `integracao/fase-1` · 27/10/2026

## Para que serve esta branch

Ela junta, a partir da `main`, o trabalho das três branches abertas. Cada uma entra num merge separado, para o histórico mostrar as partes:

1. `feat/api-triagem` (André): API FastAPI e armazenamento (modo local e OCI);
2. `feature/agente-deploy-ingrid` (Ingrid): grafo LangGraph, leitura de PDF e imagem, prompts e deploy;
3. `feature/documentos-guilherme` (Guilherme): tela Streamlit e exemplos.

**Esta branch não vai para a `main`.** Ela existe para cada pessoa baixar, rodar tudo junto na própria máquina e ver onde as partes não se encaixam. As correções são feitas **nas branches de cada um**, e cada uma entra na `main` pelo seu próprio pull request.

> **Sobre a branch do Guilherme:** ela substituía `.env.example`, `.gitignore`, `README.md` e `requirements.txt` pelas versões antigas do zip. Nesta integração, esses 4 arquivos ficaram com a versão atual da estrutura do projeto. Os arquivos novos dele (`app.py`, `schemas.py`, `api_client.py` e `EXEMPLOS_DEMO.md`) entraram como estão, na raiz. Detalhes no item E9 de [`erros.md`](erros.md).

---

## Pré-requisitos

- **Python 3.13**
- Git

```bash
python3.13 --version     # Linux ou macOS
py -3.13 --version       # Windows
```

## 1. Baixar a branch

Quem já tem o repositório clonado, na raiz dele:

```bash
git fetch origin
git switch integracao/fase-1
```

Quem ainda não tem:

```bash
git clone https://github.com/No-Country-simulation/g10-Brasil27.git
cd g10-Brasil27
git switch integracao/fase-1
```

## 2. Criar o ambiente virtual e instalar as dependências

O `requirements.txt` desta branch junta as dependências de todos: API, OCI, LangGraph, PDF e imagem. Mesmo quem já tem uma `.venv` precisa rodar o `pip install` de novo.

Linux ou macOS:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows (PowerShell):

```powershell
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 3. Configurar o `.env`

```bash
cp .env.example .env          # Linux ou macOS
copy .env.example .env        # Windows
```

**Não é preciso preencher nada para rodar localmente:**

- `MEDIFLOW_ARMAZENAMENTO` vazio = modo `local`. A API grava os documentos em `armazenamento_local/`, sem nenhuma credencial da OCI. O modo `oci` usa os buckets da conta do André e só funciona na máquina dele.
- `LLM_API_KEY` vazio: o grafo da Ingrid usa um **fallback determinístico**, sem chamar o Gemini. Para testar com o Gemini de verdade, coloque **a sua própria chave** em `LLM_API_KEY` (cada pessoa usa um projeto próprio no Google AI Studio). Nunca use dados reais de pacientes.

## 4. Rodar os testes

Sempre a partir da raiz do repositório, com a `.venv` ativada:

```bash
python -m pytest -v
```

**Resultado esperado:** `89 passed` (83 da API e do armazenamento, 3 das regras e 6 do grafo).

As linhas `ERROR ... Falha de armazenamento` que aparecem durante os testes são **logs esperados** dos testes de falha da API, e não erros.

Os testes passando **não** garantem que as partes conversam entre si. É isso que os itens de [`erros.md`](erros.md) mostram.

## 5. Rodar a API

```bash
python -m uvicorn api.main:app --reload
```

Em outro terminal, ou no navegador:

- Saúde: `http://localhost:8000/api/v1/saude` → `{"status":"ok","armazenamento":"local"}`
- Documentação interativa: `http://localhost:8000/docs`. Em `POST /api/v1/triagem` → *Try it out*, cole o `requisicao_entrada` de qualquer `dados_teste/*/exemplo.json`.

Pelo terminal (Linux ou macOS), enviando o cenário de urgência:

```bash
python -c "import json; print(json.dumps(json.load(open('dados_teste/2_urgencia/exemplo.json'))['requisicao_entrada']))" | curl -s -X POST http://localhost:8000/api/v1/triagem -H "Content-Type: application/json" -d @-
```

O mesmo `documento_id` enviado duas vezes responde **409**, porque nada é sobrescrito. Para enviar de novo, troque o ID ou apague a pasta `armazenamento_local/`.

> A API ainda usa o **agente simulado** (`api/agente_simulado.py`), e não o grafo da Ingrid. Ver o item E7 de [`erros.md`](erros.md).

## 6. Rodar o grafo da Ingrid direto, sem a API

```bash
python -c "import json; from contratos.modelos import DocumentoEntrada; from agente import executar_triagem_mediflow; e = DocumentoEntrada(**json.load(open('dados_teste/2_urgencia/exemplo.json'))['requisicao_entrada']); print(executar_triagem_mediflow(e).model_dump_json(indent=2))"
```

Troque `2_urgencia` por `1_rotina` ou `3_auditoria_humana` para ver os outros cenários.

## 7. O que ainda não funciona nesta branch

| Parte | Situação | Itens |
|---|---|---|
| Tela Streamlit (`app.py`) | Não abre (erro de import) e, depois de corrigido, chama a rota errada | E1, E2, E3 |
| Docker (`deploy/`) | O container da tela aponta para um arquivo que não existe; o healthcheck da API chama uma rota que não existe | E4, E5 |
| API + grafo | A API ainda não chama o grafo | E6, E7 |
| Regras de urgência | Falsos positivos e falsos negativos com textos comuns | L1 a L6 |

Lista completa, com o comando para reproduzir cada erro: [`erros.md`](erros.md).

## Limpeza

A pasta `armazenamento_local/` pode ser apagada a qualquer momento, e ela não vai para o Git. O `.env` também não vai para o Git.

---

*Os comandos deste documento foram executados no Linux (Python 3.13). Os comandos para Windows seguem o padrão do README e não foram testados num Windows.*
