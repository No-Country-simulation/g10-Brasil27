# Integração da Fase 1 — Erros encontrados

**Branch:** `integracao/fase-1` · 27/10/2026

Encontrados ao juntar `main` + `feat/api-triagem` + `feature/agente-deploy-ingrid` + `feature/documentos-guilherme` e rodar tudo junto. **Os testes automatizados passam (89 passed)**, mas as partes ainda não se encaixam.

**Todos os comandos abaixo foram executados nesta branch e produziram exatamente o resultado mostrado.** Rode-os a partir da raiz do repositório, com a `.venv` ativada e o `.env` copiado do `.env.example` (ver [`como-rodar.md`](como-rodar.md)).

Cada item traz: **o que acontece**, **como reproduzir**, **o que deveria acontecer**, **de quem é** e uma **sugestão**. As sugestões são propostas, e a decisão é de quem é dono da parte e da equipe.

## Resumo

| # | Problema | De quem |
|---|---|---|
| E1 | A tela não abre: import de módulo que não existe | Guilherme |
| E2 | A tela chama `/triagem`; a API está em `/api/v1/triagem` | Guilherme |
| E3 | A tela envia arquivo em multipart; a API só aceita JSON | Equipe decide |
| E4 | O Docker roda `interface/app.py`, que não existe | Ingrid + Guilherme |
| E5 | O healthcheck do Docker chama `/health`, que não existe | Ingrid |
| E6 | O grafo informa `status_backup="sucesso"` sem gravar nada | Ingrid |
| E7 | A API ainda não chama o grafo | André + Ingrid |
| E8 | O deploy abre as portas 8000 e 8501 para a internet, com a API sem autenticação | Ingrid + André |
| E9 | A branch original do Guilherme substitui 4 arquivos de configuração | Guilherme |
| L1–L6 | Regras de urgência: falsos positivos e falsos negativos | Lethicia |

---

## E1 — A tela não abre

**O que acontece:** o `app.py` importa `prompts.classificacao` e `prompts.extracao`. Esses módulos não existem no repositório: a pasta `prompts/` só tem o `extracao_clinica.py` da Ingrid. O Streamlit para na primeira linha de import.

**Como reproduzir:**

```bash
python -c "import prompts.classificacao"
```

```text
ModuleNotFoundError: No module named 'prompts.classificacao'
```

**Deveria:** a tela abrir com `python -m streamlit run interface/app.py`.

**De quem:** Guilherme.

**Sugestão:** subir os prompts para `prompts/`, ou passar a usar os da Ingrid (`prompts/extracao_clinica.py`). Combinar com a Ingrid qual conjunto de prompts o grafo usa, para existir um só.

---

## E2 — A tela chama a rota errada

**O que acontece:** a tela e o `api_client.py` chamam `/triagem` (padrão de `MEDIFLOW_TRIAGE_PATH`). A rota da API é `/api/v1/triagem`.

**Como reproduzir:**

```bash
python -c "from fastapi.testclient import TestClient; from api.main import app; print(TestClient(app).post('/triagem', json={}).status_code)"
```

```text
404
```

**Deveria:** a tela chamar `POST /api/v1/triagem`.

**De quem:** Guilherme.

**Sugestão:** trocar o caminho padrão para `/api/v1/triagem` e remover a variável `MEDIFLOW_TRIAGE_PATH`, que não está no `.env.example`. A tela passa a usar só `MEDIFLOW_API_URL`.

---

## E3 — A tela envia arquivo num formato que a API não aceita

**O que acontece:** para PDF e imagem, a tela envia `multipart/form-data` (campo `arquivo`). A API segue o contrato da Lethicia e recebe **JSON**, com o arquivo em `documento_base64`.

**Como reproduzir:**

```bash
python -c "from fastapi.testclient import TestClient; from api.main import app; r = TestClient(app).post('/api/v1/triagem', data={'documento_id': 'DOC-1'}, files={'arquivo': ('x.pdf', b'%PDF-1.4', 'application/pdf')}); print(r.status_code)"
```

```text
422
```

**Deveria:** o envio de arquivo pela tela funcionar.

**De quem:** decisão da equipe; a implementação fica com o André (API) ou com o Guilherme (tela), conforme a decisão.

**Sugestão:** escolher um dos dois caminhos:
- **a)** a tela converte o arquivo para Base64 e envia JSON, como diz o contrato (mudança só na tela);
- **b)** a API ganha um segundo endpoint, `POST /api/v1/triagem/arquivo`, em multipart (mudança só na API; o envio de arquivos grandes fica mais leve).

---

## E4 — O Docker aponta para uma tela que não existe

**O que acontece:** o `docker-compose.yml` sobe a tela com `interface/app.py`, mas a pasta `interface/` só tem o `.gitkeep`. O `app.py` do Guilherme está na raiz.

**Como reproduzir:**

```bash
grep -n 'interface/app.py' deploy/docker-compose.yml
ls -A interface/
```

```text
56:      - "interface/app.py"
.gitkeep
```

**Deveria:** o caminho do compose e a localização do arquivo serem os mesmos.

**De quem:** Ingrid + Guilherme.

**Sugestão:** manter `interface/app.py`, que segue a estrutura do projeto, e o Guilherme mover o `app.py` para lá.

---

## E5 — O healthcheck do Docker vai marcar a API como "unhealthy"

**O que acontece:** o `HEALTHCHECK` do `Dockerfile` chama `/health`. A rota de saúde da API é `/api/v1/saude`.

**Como reproduzir:**

```bash
grep -n 'health' deploy/Dockerfile
python -c "from fastapi.testclient import TestClient; from api.main import app; c = TestClient(app); print('/health ->', c.get('/health').status_code, '| /api/v1/saude ->', c.get('/api/v1/saude').status_code)"
```

```text
56:    CMD curl -fsS http://localhost:8000/health || exit 1
/health -> 404 | /api/v1/saude -> 200
```

**Deveria:** o healthcheck responder 200 com a API no ar.

**De quem:** Ingrid.

**Sugestão:** trocar para `http://localhost:8000/api/v1/saude`.

---

## E6 — O grafo informa gravação com sucesso sem ter gravado

**O que acontece:** os nós de roteamento do grafo preenchem `armazenamento_oci` com `status_backup="sucesso"`, mas o grafo não grava nada. Além disso, usa o layout antigo, com um bucket único e prefixos.

**Como reproduzir:**

```bash
python -c "import json; from contratos.modelos import DocumentoEntrada; from agente import executar_triagem_mediflow; e = DocumentoEntrada(**json.load(open('dados_teste/2_urgencia/exemplo.json'))['requisicao_entrada']); print(executar_triagem_mediflow(e).armazenamento_oci)"
```

```text
bucket='mediflow-documentos-clinicos' caminho_objeto='processados/urgentes/DOC-CLIN-2026-8942.json' status_backup='sucesso'
```

**Deveria:** só quem gravou de fato informar `status_backup`. Hoje, quem grava é a API (`armazenamento/`), num bucket por status: `mediflow-urgentes`, `mediflow-rotina`, `mediflow-auditoria-humana`.

**De quem:** Ingrid. Os trechos estão em `agente/grafo.py`, linhas 165, 208 e 238.

**Sugestão:** o grafo deixa `armazenamento_oci=None`; a API grava e preenche o campo com o resultado real.

---

## E7 — A API ainda não chama o grafo

**O que acontece:** a API usa o agente simulado (`api/agente_simulado.py`). O grafo da Ingrid tem outra interface:

| | Assinatura | Devolve |
|---|---|---|
| Simulador da API | `analisar_documento(entrada)` | classificação + dados extraídos; a API chama as regras |
| Grafo da Ingrid | `executar_triagem_mediflow(entrada)` | a `TriagemResposta` completa, já com o roteamento (o grafo chama as regras) |

**Como reproduzir:** compare `api/triagem.py` (a chamada a `analisar_documento`) com `agente/grafo.py` (a função `executar_triagem_mediflow`).

**Deveria:** a API chamar o grafo real.

**De quem:** André (API) + Ingrid (grafo).

**Sugestão:** a API chama `executar_triagem_mediflow(entrada)` e passa a fazer só o que é dela: gravar a entrada, gravar o resultado no bucket do destino e preencher `armazenamento_oci` com o resultado real (depende do E6). Isso segue a fronteira do plano de fases: **o grafo decide, a API executa**.

---

## E8 — O deploy expõe a API à internet sem proteção

**O que acontece:** o script de provisionamento libera no firewall as portas 8000 (API) e 8501 (tela) direto para a internet, além das portas 80 e 443 do nginx. A API ainda não tem autenticação nem limite de tamanho do corpo da requisição.

**Como reproduzir:**

```bash
grep -n 'ufw allow' deploy/setup_oci_vm.sh
```

```text
56:sudo ufw allow 22/tcp comment "SSH Admin"
57:sudo ufw allow 80/tcp comment "Nginx Reverse Proxy HTTP"
58:sudo ufw allow 443/tcp comment "HTTPS"
59:sudo ufw allow 8000/tcp comment "MediFlow FastAPI"
60:sudo ufw allow 8501/tcp comment "MediFlow Streamlit UI"
```

**Por que importa:** a conta OCI que guarda os buckets é **Pay As You Go**. Qualquer pessoa na internet poderia enviar documentos em massa, ocupar armazenamento e gastar requisições acima do Free Tier, que é cobrado no cartão. O Free Tier é regra do hackathon.

**De quem:** Ingrid (deploy) + André (API).

**Sugestão:**
- só o nginx (80/443) fica exposto, e as portas 8000 e 8501 deixam de ser liberadas no `ufw`;
- a API ganha uma chave de acesso simples e um limite de tamanho do corpo **antes** de qualquer deploy público;
- a equipe define **em qual conta OCI e em qual VM** o deploy acontece. O André planejou a dele, onde já estão os buckets.

---

## E9 — A branch original do Guilherme substitui 4 arquivos de configuração

**O que acontece:** o commit "Add files via upload" coloca na raiz o conteúdo do zip e **substitui** `.env.example`, `.gitignore`, `README.md` e `requirements.txt` pelas versões antigas. Ao juntar com as outras branches, dá conflito nos 4 arquivos. Nesta integração, eles ficaram com a versão atual. Se a branch fosse mergeada como está:

- o `.env.example` perderia as variáveis da API e do OCI;
- o `.gitignore` voltaria a bloquear `*.pdf` e `*.png`, e os cenários de `dados_teste/` não entrariam no Git;
- o `requirements.txt` voltaria a faixas de versão e perderia `fastapi`, `oci`, `langgraph` etc.;
- o `README.md` perderia a estrutura e as instruções de execução.

**Como reproduzir:**

```bash
git diff --stat origin/main origin/feature/documentos-guilherme
```

**Deveria:** a branch acrescentar só os arquivos dele, na estrutura do projeto.

**De quem:** Guilherme.

**Sugestão:** refazer a branch a partir da `main` atual, com os arquivos em `interface/` (`app.py` e `api_client.py`), em `prompts/` (ver E1) e em `dados_teste/` (os exemplos do `EXEMPLOS_DEMO.md`), **sem** tocar nos 4 arquivos de configuração. O `schemas.py` sai, porque o contrato já está em `contratos/modelos.py`.

---

## L1–L6 — Regras de urgência (`regras/regras_clinicas.py`)

**De quem:** Lethicia. Essas regras **já estão na `main`**, e o grafo da Ingrid as usa, então os problemas aparecem também no grafo.

A busca de termos usa `termo in texto`, sem separar palavras, sem remover acentos e sem tratar negação. Cada comando abaixo chama `detectar_urgencia_clinica`, que devolve `(é_urgente, motivo)`.

| # | Texto de exemplo | Deveria | Obtido |
|---|---|---|---|
| L1 | `Tomar 1 comprimido de Losartana 50mg diariamente.` | não urgente | **urgente (IAM)**: "diar**iam**ente" contém "iam" |
| L2 | `Hemograma normal. PCR: 3,2 mg/L.` | não urgente (PCR = Proteína C Reativa) | **urgente (PCR)**, lido como parada cardiorrespiratória |
| L3 | `Paciente evoluiu com choque séptico.` | **urgente** | **não urgente**: o termo da lista está sem acento ("choque septico") |
| L4 | `Ausencia de sinais de TEP.` | não urgente (exame normal) | **urgente (TEP)**: a negação é ignorada |
| L5 | `Sinusite leve, sem sinais de gravidade.` | não urgente | **urgente ('gravidade')**: termos "prioritários" também vão para a emergência |

**Como reproduzir** (troque o texto entre aspas simples por qualquer linha da tabela):

```bash
python -c "from contratos.modelos import DadosExtraidos; from regras.regras_clinicas import detectar_urgencia_clinica; print(detectar_urgencia_clinica('Tomar 1 comprimido de Losartana 50mg diariamente.', DadosExtraidos()))"
```

```text
(True, 'Achado crítico de alta gravidade (IAM) detectado em paciente sintomático.')
```

**L6 — Validação de CRM aceita qualquer número.** O padrão `\d{3,8}` aceita qualquer texto com 3 dígitos seguidos.

```bash
python -c "from regras.regras_clinicas import validar_crm; print(validar_crm('123'))"
```

```text
(True, 'CRM Válido')
```

**Sugestões:**
- remover acentos dos dois lados antes de comparar (`unicodedata`);
- buscar a palavra inteira, com `\b` no regex;
- tratar as negações mais comuns antes do termo ("sem", "ausência de", "afastado", "não há");
- separar os termos prioritários dos críticos: prioritário não vai para a fila de emergência;
- tirar "PCR" da lista ou exigir contexto;
- validar o CRM no formato número + UF (ex.: `145892-SP`);
- quando a regra detectar urgência, atualizar também o `nivel_prioridade`;
- cada linha da tabela acima vira um teste em `tests/test_regras.py`, para a correção provar que funcionou.

**Também vale alinhar:** os `exemplo.json` de `dados_teste/` ainda mostram o layout de bucket único (`mediflow-documentos-clinicos` + `processados/...`). A API grava um bucket por status, como pede o edital ("Crie buckets ... por status").
