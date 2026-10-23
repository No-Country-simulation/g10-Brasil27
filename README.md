# 🏥 MediFlow – Agente Autônomo para Triagem, Extração e Roteamento de Documentos Clínicos

> **Hackathon ONE (Grupo 10) – Oracle Next Education & Alura**  
> **Equipe:** `g10-Brasil27`

---

## 📌 Sobre o Projeto

O **MediFlow** é um agente autônomo desenvolvido para receber documentos clínicos e administrativos em texto, PDF ou imagem, classificá-los automaticamente, extrair entidades clínicas essenciais e roteá-los para o setor hospitalar adequado.

O sistema conta com validação condicional e fluxo **Human-in-the-Loop (HITL)** para reter casos ambíguos ou ilegíveis para revisão humana, priorizar alertas de urgência médica e armazenar os documentos de forma segregada no **Oracle Cloud Infrastructure (OCI) Object Storage (Camada Always Free)**.

---

## 🧠 Fluxo de Decisão do Agente

```mermaid
graph TD
    A[📄 Ingestão do Documento<br/>Texto / PDF / Imagem] --> B[🤖 Agente Multimodal LLM<br/>Classificação + Extração de Dados]
    B --> C[📐 Validação Estruturada<br/>JSON Schema]
    C --> D{Score de Confiança Adequado<br/>E Dados Consistentes?}

    D -- Não (Ambíguo / Ilegível) --> E[⚠️ Fila de Revisão Humana<br/>Human-in-the-Loop]
    E --> F[(☁️ OCI Object Storage<br/>auditoria_humana/)]

    D -- Sim --> G{Avaliação de Prioridade Clínica}

    G -- Urgente --> H[🚨 Fila de Emergência Médica<br/>Alerta ao Plantão]
    H --> I[(☁️ OCI Object Storage<br/>processados/urgentes/)]

    G -- Rotina --> J[🏥 Roteamento Automatizado<br/>Farmácia / Autorizações / PEP]
    J --> K[(☁️ OCI Object Storage<br/>processados/rotina/)]
```

---

## 📂 Estrutura do Repositório

```text
g10-Brasil27/
├── contratos/       # Modelos Pydantic de entrada e saída (contrato de dados)
├── regras/          # Regras de consistência, score de confiança e critérios de urgência
├── agente/          # Grafo de decisão e leitura de documentos (texto / PDF / imagem)
├── prompts/         # Prompts de classificação e extração
├── api/             # FastAPI: endpoints, execução do roteamento e alertas
├── armazenamento/   # Persistência no OCI Object Storage (Always Free)
├── interface/       # Telas Streamlit de envio e de auditoria
├── dados_teste/     # Cenários obrigatórios da demonstração (somente dados fictícios)
│   ├── 1_rotina/
│   ├── 2_urgencia/
│   └── 3_auditoria_humana/
├── deploy/          # Docker e configuração da VM na OCI
├── docs/            # Documentação complementar
└── tests/           # Testes automatizados
```

As pastas importadas por outras partes (`contratos/`, `regras/`, `agente/`, `prompts/`, `api/` e `armazenamento/`) têm um arquivo `__init__.py`.

---

## ▶️ Como Executar

### Pré-requisitos

- **Python 3.13**
- Git

Para conferir a versão do Python:

```bash
python3.13 --version     # Linux ou macOS
py -3.13 --version       # Windows
```

### 1. Criar o ambiente virtual e instalar as dependências

Na raiz do repositório.

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

### 2. Configurar as variáveis de ambiente

Copie o `.env.example` para `.env` e preencha os valores somente na sua máquina. O `.env` nunca vai para o Git.

```bash
cp .env.example .env
```

### 3. Executar

Sempre a partir da raiz do repositório, com a `.venv` ativada e usando `python -m`:

```bash
python -m uvicorn api.main:app --reload      # API
python -m streamlit run interface/app.py     # Interface
python -m pytest                             # Testes
```

Executado com `python -m`, o Python inclui a pasta atual no caminho de importação. Assim, imports entre pastas (por exemplo, `from contratos.modelos import ...`) funcionam em qualquer parte do projeto.

---

## 🧪 Casos de Teste (MVP)

1. **Cenário 1 – Rotina (`dados_teste/1_rotina`):** Fluxo padrão aprovado e encaminhado automaticamente.
2. **Cenário 2 – Urgência Médica (`dados_teste/2_urgencia`):** Identificação de achado crítico com disparo de alerta de emergência.
3. **Cenário 3 – Auditoria Humana (`dados_teste/3_auditoria_humana`):** Caso ambíguo ou com baixa confiabilidade direcionado para revisão humana.

> Somente documentos fictícios. Nenhum dado real de paciente entra no repositório nem passa pelo sistema.
