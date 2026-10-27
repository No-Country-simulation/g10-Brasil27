"""
MediFlow - Testes da camada de armazenamento
Hackathon ONE G10 - Grupo 10: MediFlow

Mapeamento: tests/test_armazenamento.py
Rodam sem rede e sem credenciais OCI: o RepositorioOCI é testado com um cliente falso.
Execução (a partir da raiz): python -m pytest tests/test_armazenamento.py -v
"""

import json
import subprocess
import sys
from pathlib import Path

import oci
import pytest

from armazenamento.repositorio import (
    FalhaArmazenamento,
    ObjetoJaExiste,
    RepositorioLocal,
    RepositorioOCI,
    criar_repositorio,
    obter_buckets,
)

RAIZ = Path(__file__).resolve().parent.parent

VARIAVEIS = (
    "MEDIFLOW_ARMAZENAMENTO",
    "MEDIFLOW_ARMAZENAMENTO_LOCAL_DIR",
    "OCI_AUTH",
    "OCI_CONFIG_FILE",
    "OCI_CONFIG_PROFILE",
    "OCI_BUCKET_PREFIXO",
    "OCI_NAMESPACE",
)

CONTEUDO = {"documento_id": "DOC-1", "texto": "Laudo de ação rápida", "itens": [1, 2]}


@pytest.fixture(autouse=True)
def ambiente_limpo(monkeypatch):
    # contratos/modelos.py chama load_dotenv() ao ser importado: o .env de quem roda os
    # testes (por exemplo, MEDIFLOW_ARMAZENAMENTO=oci) não pode influenciar o resultado.
    for variavel in VARIAVEIS:
        monkeypatch.delenv(variavel, raising=False)


# ============================================================================
# RepositorioLocal
# ============================================================================

def test_local_grava_e_o_json_volta_igual(tmp_path):
    RepositorioLocal(tmp_path).salvar_json("mediflow-rotina", "DOC-1.json", CONTEUDO)

    arquivo = tmp_path / "mediflow-rotina" / "DOC-1.json"
    texto = arquivo.read_text(encoding="utf-8")
    assert json.loads(texto) == CONTEUDO
    assert "ação rápida" in texto  # ensure_ascii=False
    assert '\n  "documento_id"' in texto  # indent=2


def test_local_segunda_gravacao_levanta_objeto_ja_existe_e_preserva_o_primeiro(tmp_path):
    repositorio = RepositorioLocal(tmp_path)
    repositorio.salvar_json("mediflow-rotina", "DOC-1.json", CONTEUDO)
    arquivo = tmp_path / "mediflow-rotina" / "DOC-1.json"
    original = arquivo.read_bytes()

    with pytest.raises(ObjetoJaExiste):
        repositorio.salvar_json("mediflow-rotina", "DOC-1.json", {"outro": "conteudo"})

    assert arquivo.read_bytes() == original


@pytest.mark.parametrize(
    "nome_objeto",
    ["../fora.json", "../../fora.json", "../mediflow-urgentes/fora.json", "/tmp/fora.json"],
)
def test_local_recusa_nome_que_sai_da_pasta_do_bucket(tmp_path, nome_objeto):
    base = tmp_path / "base"
    base.mkdir()

    with pytest.raises(FalhaArmazenamento):
        RepositorioLocal(base).salvar_json("mediflow-rotina", nome_objeto, CONTEUDO)

    assert list(base.rglob("*.json")) == []
    assert not (tmp_path / "fora.json").exists()


def test_local_erro_de_disco_vira_falha_armazenamento(tmp_path):
    arquivo_no_lugar_da_pasta = tmp_path / "base"
    arquivo_no_lugar_da_pasta.write_text("sou um arquivo, não uma pasta")

    with pytest.raises(FalhaArmazenamento):
        RepositorioLocal(arquivo_no_lugar_da_pasta).salvar_json("mediflow-rotina", "DOC-1.json", CONTEUDO)


def test_local_conteudo_nao_serializavel_vira_falha_e_nao_deixa_arquivo(tmp_path):
    with pytest.raises(FalhaArmazenamento):
        RepositorioLocal(tmp_path).salvar_json("mediflow-rotina", "DOC-1.json", {"x": object()})

    assert list(tmp_path.rglob("*.json")) == []


def test_local_expoe_o_nome():
    assert RepositorioLocal(Path("qualquer")).nome == "local"


# ============================================================================
# RepositorioLocal.apagar
# ============================================================================

def test_local_apagar_remove_so_o_objeto_pedido(tmp_path):
    repositorio = RepositorioLocal(tmp_path)
    repositorio.salvar_json("mediflow-recebidos", "DOC-1.json", CONTEUDO)
    repositorio.salvar_json("mediflow-recebidos", "DOC-2.json", CONTEUDO)

    repositorio.apagar("mediflow-recebidos", "DOC-1.json")

    assert not (tmp_path / "mediflow-recebidos" / "DOC-1.json").exists()
    assert (tmp_path / "mediflow-recebidos" / "DOC-2.json").exists()


def test_local_apagar_permite_gravar_de_novo_o_mesmo_objeto(tmp_path):
    repositorio = RepositorioLocal(tmp_path)
    repositorio.salvar_json("mediflow-recebidos", "DOC-1.json", CONTEUDO)
    repositorio.apagar("mediflow-recebidos", "DOC-1.json")

    repositorio.salvar_json("mediflow-recebidos", "DOC-1.json", {"novo": True})

    assert json.loads((tmp_path / "mediflow-recebidos" / "DOC-1.json").read_text(encoding="utf-8")) == {"novo": True}


def test_local_apagar_objeto_inexistente_nao_da_erro(tmp_path):
    RepositorioLocal(tmp_path).apagar("mediflow-recebidos", "NAO-EXISTE.json")

    RepositorioLocal(tmp_path).apagar("bucket-que-nao-existe", "NAO-EXISTE.json")


@pytest.mark.parametrize(
    "nome_objeto",
    ["../fora.json", "../../fora.json", "../mediflow-urgentes/DOC-1.json", "/tmp/fora.json"],
)
def test_local_apagar_recusa_nome_que_sai_da_pasta_do_bucket(tmp_path, nome_objeto):
    base = tmp_path / "base"
    repositorio = RepositorioLocal(base)
    repositorio.salvar_json("mediflow-urgentes", "DOC-1.json", CONTEUDO)  # de OUTRO bucket
    repositorio.salvar_json("mediflow-recebidos", "DOC-1.json", CONTEUDO)
    (tmp_path / "fora.json").write_text("{}")

    with pytest.raises(FalhaArmazenamento):
        repositorio.apagar("mediflow-recebidos", nome_objeto)

    assert (base / "mediflow-urgentes" / "DOC-1.json").exists()
    assert (base / "mediflow-recebidos" / "DOC-1.json").exists()
    assert (tmp_path / "fora.json").exists()


def test_local_apagar_erro_de_disco_vira_falha_armazenamento(tmp_path):
    (tmp_path / "mediflow-recebidos" / "DOC-1.json").mkdir(parents=True)  # é pasta, não arquivo

    with pytest.raises(FalhaArmazenamento) as capturada:
        RepositorioLocal(tmp_path).apagar("mediflow-recebidos", "DOC-1.json")

    assert "apagar" in str(capturada.value)


# ============================================================================
# RepositorioOCI com cliente falso (sem rede)
# ============================================================================

class ClienteFalso:
    def __init__(self, erro=None):
        self.erro = erro
        self.chamadas = []
        self.chamadas_delete = []

    def put_object(self, *args, **kwargs):
        self.chamadas.append((args, kwargs))
        if self.erro is not None:
            raise self.erro

    def delete_object(self, *args, **kwargs):
        self.chamadas_delete.append((args, kwargs))
        if self.erro is not None:
            raise self.erro


def test_oci_chama_put_object_com_os_argumentos_esperados():
    cliente = ClienteFalso()
    repositorio = RepositorioOCI(cliente, "namespace-teste")

    repositorio.salvar_json("mediflow-urgentes", "DOC-1.json", CONTEUDO)

    assert repositorio.nome == "oci"
    assert len(cliente.chamadas) == 1
    args, kwargs = cliente.chamadas[0]
    assert args[:3] == ("namespace-teste", "mediflow-urgentes", "DOC-1.json")
    assert isinstance(args[3], bytes)
    assert json.loads(args[3].decode("utf-8")) == CONTEUDO
    assert "ação rápida" in args[3].decode("utf-8")  # UTF-8 sem escape
    assert kwargs == {"content_type": "application/json", "if_none_match": "*"}


@pytest.mark.parametrize("status", [412, 409])
def test_oci_412_e_409_viram_objeto_ja_existe(status):
    erro = oci.exceptions.ServiceError(status, "ObjetoExistente", {}, "mensagem original")
    repositorio = RepositorioOCI(ClienteFalso(erro), "namespace-teste")

    with pytest.raises(ObjetoJaExiste):
        repositorio.salvar_json("mediflow-rotina", "DOC-1.json", CONTEUDO)


@pytest.mark.parametrize("status", [500, 403, 404])
def test_oci_outros_erros_viram_falha_sem_vazar_o_texto_original(status):
    segredo = "ocid1.tenancy.oc1..aaaaSEGREDO detalhe interno do servico"
    erro = oci.exceptions.ServiceError(status, "CodigoDoErro", {}, segredo)
    repositorio = RepositorioOCI(ClienteFalso(erro), "namespace-teste")

    with pytest.raises(FalhaArmazenamento) as capturada:
        repositorio.salvar_json("mediflow-rotina", "DOC-1.json", CONTEUDO)

    mensagem = str(capturada.value)
    assert f"status={status}" in mensagem
    assert "CodigoDoErro" in mensagem
    assert "SEGREDO" not in mensagem
    assert "ocid1" not in mensagem


def test_oci_erro_de_rede_vira_falha_sem_vazar_o_texto_original():
    erro = oci.exceptions.RequestException("falha com chave=ABC123 no endereco interno")
    repositorio = RepositorioOCI(ClienteFalso(erro), "namespace-teste")

    with pytest.raises(FalhaArmazenamento) as capturada:
        repositorio.salvar_json("mediflow-rotina", "DOC-1.json", CONTEUDO)

    assert "ABC123" not in str(capturada.value)
    assert "RequestException" in str(capturada.value)


# ============================================================================
# RepositorioOCI.apagar com cliente falso (sem rede)
# ============================================================================

def test_oci_apagar_chama_delete_object_com_os_argumentos_esperados():
    cliente = ClienteFalso()

    RepositorioOCI(cliente, "namespace-teste").apagar("mediflow-recebidos", "DOC-1.json")

    assert cliente.chamadas_delete == [(("namespace-teste", "mediflow-recebidos", "DOC-1.json"), {})]
    assert cliente.chamadas == []  # não gravou nada


def test_oci_apagar_404_nao_da_erro_porque_o_objeto_ja_nao_existe():
    erro = oci.exceptions.ServiceError(404, "ObjectNotFound", {}, "mensagem original")
    cliente = ClienteFalso(erro)

    RepositorioOCI(cliente, "namespace-teste").apagar("mediflow-recebidos", "DOC-1.json")

    assert len(cliente.chamadas_delete) == 1


@pytest.mark.parametrize("status", [500, 403, 409])
def test_oci_apagar_outros_erros_viram_falha_sem_vazar_o_texto_original(status):
    segredo = "ocid1.tenancy.oc1..aaaaSEGREDO detalhe interno do servico"
    erro = oci.exceptions.ServiceError(status, "CodigoDoErro", {}, segredo)
    repositorio = RepositorioOCI(ClienteFalso(erro), "namespace-teste")

    with pytest.raises(FalhaArmazenamento) as capturada:
        repositorio.apagar("mediflow-recebidos", "DOC-1.json")

    mensagem = str(capturada.value)
    assert f"status={status}" in mensagem
    assert "CodigoDoErro" in mensagem
    assert "SEGREDO" not in mensagem
    assert "ocid1" not in mensagem


def test_oci_apagar_erro_de_rede_vira_falha_sem_vazar_o_texto_original():
    erro = oci.exceptions.RequestException("falha com chave=ABC123 no endereco interno")
    repositorio = RepositorioOCI(ClienteFalso(erro), "namespace-teste")

    with pytest.raises(FalhaArmazenamento) as capturada:
        repositorio.apagar("mediflow-recebidos", "DOC-1.json")

    assert "ABC123" not in str(capturada.value)
    assert "RequestException" in str(capturada.value)


# ============================================================================
# Nomes dos buckets
# ============================================================================

def test_buckets_com_prefixo_padrao():
    buckets = obter_buckets()

    assert buckets.recebidos == "mediflow-recebidos"
    assert buckets.urgentes == "mediflow-urgentes"
    assert buckets.rotina == "mediflow-rotina"
    assert buckets.auditoria_humana == "mediflow-auditoria-humana"
    assert buckets.rejeitados == "mediflow-rejeitados"


def test_buckets_respeitam_o_prefixo_do_ambiente(monkeypatch):
    monkeypatch.setenv("OCI_BUCKET_PREFIXO", "equipe")

    assert obter_buckets().auditoria_humana == "equipe-auditoria-humana"


# ============================================================================
# criar_repositorio()
# ============================================================================

def test_fabrica_sem_variaveis_devolve_local_com_pasta_padrao():
    repositorio = criar_repositorio()

    assert isinstance(repositorio, RepositorioLocal)
    assert repositorio.nome == "local"
    assert repositorio._base == Path("armazenamento_local")


def test_fabrica_aceita_o_modo_local_com_caixa_e_espacos_e_pasta_propria(monkeypatch, tmp_path):
    monkeypatch.setenv("MEDIFLOW_ARMAZENAMENTO", "  Local ")
    monkeypatch.setenv("MEDIFLOW_ARMAZENAMENTO_LOCAL_DIR", str(tmp_path))

    repositorio = criar_repositorio()

    assert isinstance(repositorio, RepositorioLocal)
    assert repositorio._base == tmp_path


def test_fabrica_com_variaveis_vazias_como_no_env_example_usa_os_padroes(monkeypatch):
    for variavel in VARIAVEIS:
        monkeypatch.setenv(variavel, "")

    repositorio = criar_repositorio()

    assert isinstance(repositorio, RepositorioLocal)
    assert repositorio._base == Path("armazenamento_local")
    assert obter_buckets().rotina == "mediflow-rotina"


def test_fabrica_valor_invalido_levanta_value_error(monkeypatch):
    monkeypatch.setenv("MEDIFLOW_ARMAZENAMENTO", "s3")

    with pytest.raises(ValueError, match="MEDIFLOW_ARMAZENAMENTO"):
        criar_repositorio()


def test_fabrica_oci_auth_invalido_levanta_value_error(monkeypatch):
    monkeypatch.setenv("MEDIFLOW_ARMAZENAMENTO", "oci")
    monkeypatch.setenv("OCI_AUTH", "senha")

    with pytest.raises(ValueError, match="OCI_AUTH"):
        criar_repositorio()


class FabricaClienteFalso:
    """Substitui ObjectStorageClient e registra como foi criado e quantas vezes pediu o namespace."""

    instancias = []

    def __init__(self, config=None, **kwargs):
        self.config = config
        self.kwargs = kwargs
        self.chamadas_get_namespace = 0
        FabricaClienteFalso.instancias.append(self)

    def get_namespace(self):
        self.chamadas_get_namespace += 1
        return type("Resposta", (), {"data": "namespace-descoberto"})()


@pytest.fixture
def cliente_oci_falso(monkeypatch):
    FabricaClienteFalso.instancias = []
    monkeypatch.setattr(oci.object_storage, "ObjectStorageClient", FabricaClienteFalso)
    return FabricaClienteFalso


def test_fabrica_oci_api_key_le_o_perfil_e_pede_o_namespace_uma_vez(monkeypatch, cliente_oci_falso):
    chamadas = {}

    def from_file_falso(file_location, profile_name):
        chamadas["from_file"] = (file_location, profile_name)
        return {"config": "falsa"}

    monkeypatch.setattr(oci.config, "from_file", from_file_falso)
    monkeypatch.setenv("MEDIFLOW_ARMAZENAMENTO", "oci")
    monkeypatch.setenv("OCI_CONFIG_PROFILE", "MEDIFLOW")

    repositorio = criar_repositorio()

    assert isinstance(repositorio, RepositorioOCI)
    assert repositorio.nome == "oci"
    assert chamadas["from_file"] == (oci.config.DEFAULT_LOCATION, "MEDIFLOW")
    cliente = cliente_oci_falso.instancias[0]
    assert cliente.config == {"config": "falsa"}
    assert cliente.chamadas_get_namespace == 1
    assert repositorio._namespace == "namespace-descoberto"


def test_fabrica_oci_usa_o_namespace_do_ambiente_sem_consultar_a_nuvem(monkeypatch, cliente_oci_falso):
    monkeypatch.setattr(oci.config, "from_file", lambda file_location, profile_name: {})
    monkeypatch.setenv("MEDIFLOW_ARMAZENAMENTO", "oci")
    monkeypatch.setenv("OCI_NAMESPACE", "namespace-do-env")
    monkeypatch.setenv("OCI_CONFIG_FILE", "/caminho/qualquer/config")

    repositorio = criar_repositorio()

    assert repositorio._namespace == "namespace-do-env"
    assert cliente_oci_falso.instancias[0].chamadas_get_namespace == 0


def test_fabrica_oci_instance_principal_usa_o_signer(monkeypatch, cliente_oci_falso):
    signer_falso = object()
    monkeypatch.setattr(oci.auth.signers, "InstancePrincipalsSecurityTokenSigner", lambda: signer_falso)
    monkeypatch.setenv("MEDIFLOW_ARMAZENAMENTO", "oci")
    monkeypatch.setenv("OCI_AUTH", "instance_principal")
    monkeypatch.setenv("OCI_NAMESPACE", "namespace-do-env")

    criar_repositorio()

    cliente = cliente_oci_falso.instancias[0]
    assert cliente.config == {}
    assert cliente.kwargs == {"signer": signer_falso}


def test_fabrica_oci_erro_de_configuracao_vira_falha_sem_vazar_detalhes(monkeypatch, cliente_oci_falso):
    def from_file_quebrado(file_location, profile_name):
        raise oci.exceptions.ProfileNotFound("perfil em /home/alguem/.oci/config com ocid1.user.SEGREDO")

    monkeypatch.setattr(oci.config, "from_file", from_file_quebrado)
    monkeypatch.setenv("MEDIFLOW_ARMAZENAMENTO", "oci")

    with pytest.raises(FalhaArmazenamento) as capturada:
        criar_repositorio()

    assert "SEGREDO" not in str(capturada.value)
    assert "/home/alguem" not in str(capturada.value)


def test_modo_local_nao_importa_o_pacote_oci():
    # Processo novo: neste, o pytest já importou o `oci`.
    codigo = (
        "import sys\n"
        "from armazenamento.repositorio import criar_repositorio\n"
        "repositorio = criar_repositorio()\n"
        "assert repositorio.nome == 'local'\n"
        "assert 'oci' not in sys.modules, 'o modo local importou o oci'\n"
    )
    ambiente = {"PATH": "", "MEDIFLOW_ARMAZENAMENTO": "local"}

    resultado = subprocess.run(
        [sys.executable, "-c", codigo], cwd=RAIZ, env=ambiente, capture_output=True, text=True
    )

    assert resultado.returncode == 0, resultado.stderr
