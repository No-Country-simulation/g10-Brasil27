import os
import uuid
import requests
import streamlit as st

from prompts.classificacao import PROMPT_CLASSIFICACAO
from prompts.extracao import PROMPT_EXTRACAO

st.set_page_config(page_title="MediFlow | Triagem documental", page_icon="🏥", layout="wide")

API_URL = os.getenv("MEDIFLOW_API_URL", "http://localhost:8000")
TRIAGE_PATH = os.getenv("MEDIFLOW_TRIAGE_PATH", "/triagem")

st.title("🏥 MediFlow — Triagem de documentos clínicos")
st.caption("Protótipo de interface para demonstração. Não use dados reais de pacientes.")

with st.sidebar:
    st.header("Configuração")
    api_url = st.text_input("URL da API FastAPI", value=API_URL)
    triage_path = st.text_input("Caminho do endpoint", value=TRIAGE_PATH)
    canal_origem = st.selectbox(
        "Canal de origem",
        ["Recepcao", "Pronto_Socorro", "Ambulatorio", "Laboratorio", "Outro"],
    )
    st.divider()
    st.subheader("Prompts da equipe")
    st.caption("Os prompts estão preparados em prompts/classificacao.py e prompts/extracao.py.")
    with st.expander("Ver prompt de classificação"):
        st.code(PROMPT_CLASSIFICACAO, language="text")
    with st.expander("Ver prompt de extração"):
        st.code(PROMPT_EXTRACAO, language="text")

modo = st.radio("Como deseja fornecer o documento?", ["Texto do documento", "Enviar arquivo PDF ou imagem"], horizontal=True)

documento_texto = ""
arquivo = None
tipo_arquivo = "TEXTO"

if modo == "Texto do documento":
    documento_texto = st.text_area(
        "Conteúdo do documento (use apenas exemplos fictícios)",
        height=240,
        placeholder="Cole aqui o texto de um documento clínico fictício para a demonstração...",
    )
    tipo_arquivo = "TEXTO"
else:
    arquivo = st.file_uploader(
        "Selecione um PDF ou uma imagem",
        type=["pdf", "png", "jpg", "jpeg", "webp"],
        help="Use somente documentos sintéticos ou devidamente anonimizados.",
    )
    if arquivo:
        extensao = arquivo.name.rsplit(".", 1)[-1].lower()
        tipo_arquivo = "PDF" if extensao == "pdf" else "IMAGEM"

col1, col2 = st.columns([1, 1])
with col1:
    documento_id = st.text_input("ID do documento", value=f"DOC-DEMO-{uuid.uuid4().hex[:8].upper()}")
with col2:
    st.text_input("Status", value="Aguardando envio", disabled=True)

st.warning(
    "Este protótipo não faz diagnóstico nem substitui profissionais de saúde. "
    "A sinalização de urgência deve seguir as regras do fluxo e os responsáveis clínicos."
)

if st.button("Enviar para triagem", type="primary", use_container_width=True):
    if modo == "Texto do documento" and not documento_texto.strip():
        st.error("Insira o texto fictício do documento antes de enviar.")
        st.stop()
    if modo == "Enviar arquivo PDF ou imagem" and arquivo is None:
        st.error("Selecione um arquivo antes de enviar.")
        st.stop()

    endpoint = f"{api_url.rstrip('/')}/{triage_path.lstrip('/')}"
    try:
        with st.spinner("Enviando documento para a API MediFlow..."):
            if arquivo is not None:
                # Contrato multipart é provisório: alinhar o nome do campo e endpoint com o responsável pela API.
                files_payload = {"arquivo": (arquivo.name, arquivo.getvalue(), arquivo.type or "application/octet-stream")}
                data_payload = {
                    "documento_id": documento_id,
                    "tipo_arquivo": tipo_arquivo,
                    "canal_origem": canal_origem,
                }
                response = requests.post(endpoint, data=data_payload, files=files_payload, timeout=90)
            else:
                # Campos baseados no exemplo de entrada do PDF do projeto.
                payload = {
                    "documento_id": documento_id,
                    "tipo_arquivo": tipo_arquivo,
                    "documento_texto": documento_texto,
                    "canal_origem": canal_origem,
                }
                response = requests.post(endpoint, json=payload, timeout=90)

        if response.ok:
            resultado = response.json()
            st.success("A API retornou um resultado de triagem.")
            st.subheader("Resultado estruturado")
            st.json(resultado)

            classificacao = resultado.get("classificacao", {})
            roteamento = resultado.get("decisao_roteamento", {})
            c1, c2, c3 = st.columns(3)
            c1.metric("Tipo de documento", classificacao.get("tipo_documento", "Não informado"))
            c2.metric("Prioridade", classificacao.get("nivel_prioridade", "Não informada"))
            c3.metric(
                "Revisão humana",
                "Sim" if roteamento.get("requer_auditoria_humana", True) else "Não",
            )
        else:
            st.error(f"A API respondeu com HTTP {response.status_code}.")
            st.code(response.text[:4000])
            st.info(
                "Confirme com o responsável pelo back-end o endpoint, o formato de envio "
                "e o nome do campo de upload. Esses detalhes ainda precisam ser alinhados pela equipe."
            )
    except requests.exceptions.ConnectionError:
        st.error("Não foi possível conectar à API.")
        st.write(f"Endereço tentado: `{endpoint}`")
        st.info("Inicie a API FastAPI ou ajuste a URL no painel lateral.")
    except requests.exceptions.Timeout:
        st.error("A API demorou demais para responder. Tente novamente ou verifique os logs do back-end.")
    except ValueError:
        st.error("A resposta da API não veio em JSON válido.")
    except requests.exceptions.RequestException as exc:
        st.error(f"Erro na comunicação com a API: {exc}")

st.divider()
st.caption("MediFlow • Hackathon ONE G10 • Interface inicial de demonstração")
