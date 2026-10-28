"""
MediFlow - Camada de Armazenamento (OCI Object Storage e disco local)
Hackathon ONE G10 - Grupo 10: MediFlow

Mapeamento: armazenamento/repositorio.py
Os dois repositórios têm a mesma interface (RepositorioDocumentos). A API não sabe
qual está em uso: o modo é escolhido por variável de ambiente em criar_repositorio().
Nenhuma gravação sobrescreve um objeto existente. O método apagar() existe para a
compensação da API (api/triagem.py): desfazer a entrada quando o processamento falha.
"""

import json
import os
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class ObjetoJaExiste(Exception):
    """O objeto já existe no bucket (ou na pasta local); a gravação foi recusada."""


class FalhaArmazenamento(Exception):
    """Falha ao gravar ou apagar. A mensagem nunca contém credenciais, OCIDs nem o erro original."""


class RepositorioDocumentos(Protocol):
    """Interface comum aos repositórios de documentos."""

    nome: str

    def salvar_json(self, bucket: str, nome_objeto: str, conteudo: dict) -> None:
        """Grava `conteudo` como JSON UTF-8. Levanta ObjetoJaExiste se já existir."""
        ...

    def apagar(self, bucket: str, nome_objeto: str) -> None:
        """Apaga o objeto. Se ele já não existir, não faz nada."""
        ...


def _serializar(conteudo: dict) -> bytes:
    try:
        return json.dumps(conteudo, ensure_ascii=False, indent=2).encode("utf-8")
    except (TypeError, ValueError) as erro:
        raise FalhaArmazenamento(
            f"Conteúdo não serializável em JSON ({type(erro).__name__})."
        ) from None


def _falha_servico(erro) -> FalhaArmazenamento:
    """Só o status e o código do erro do Object Storage; nunca o texto original."""
    return FalhaArmazenamento(
        f"Falha no Object Storage (status={erro.status}, codigo={erro.code})."
    )


def _falha_comunicacao(erro: Exception) -> FalhaArmazenamento:
    """Só o nome da classe do erro de rede; nunca o texto original."""
    return FalhaArmazenamento(
        f"Falha de comunicação com o Object Storage ({type(erro).__name__})."
    )


class RepositorioLocal:
    """Grava em `diretorio_base/<bucket>/<nome_objeto>`. Usado pelos colegas e pelo CI."""

    nome = "local"

    def __init__(self, diretorio_base: Path):
        self._base = Path(diretorio_base)

    def _caminho_do_objeto(self, bucket: str, nome_objeto: str) -> Path:
        pasta = self._base / bucket
        caminho = pasta / nome_objeto

        # Defesa em profundidade: a API já valida o documento_id, mas o repositório não
        # pode gravar nem apagar fora da pasta do próprio bucket (nem na de outro) se for
        # usado sem a API.
        if not caminho.resolve().is_relative_to(pasta.resolve()):
            raise FalhaArmazenamento("Nome de objeto inválido.")
        return caminho

    def salvar_json(self, bucket: str, nome_objeto: str, conteudo: dict) -> None:
        corpo = _serializar(conteudo)
        caminho = self._caminho_do_objeto(bucket, nome_objeto)

        try:
            caminho.parent.mkdir(parents=True, exist_ok=True)
        except OSError as erro:
            raise FalhaArmazenamento(
                f"Falha ao gravar no disco local ({type(erro).__name__})."
            ) from None

        try:
            with open(caminho, "xb") as arquivo:
                arquivo.write(corpo)
        except FileExistsError:
            raise ObjetoJaExiste(f"{bucket}/{nome_objeto}") from None
        except OSError as erro:
            # Não deixa um arquivo pela metade: ele faria o reenvio virar 409.
            with suppress(OSError):
                caminho.unlink(missing_ok=True)
            raise FalhaArmazenamento(
                f"Falha ao gravar no disco local ({type(erro).__name__})."
            ) from None

    def apagar(self, bucket: str, nome_objeto: str) -> None:
        caminho = self._caminho_do_objeto(bucket, nome_objeto)
        try:
            caminho.unlink(missing_ok=True)
        except OSError as erro:
            raise FalhaArmazenamento(
                f"Falha ao apagar no disco local ({type(erro).__name__})."
            ) from None


class RepositorioOCI:
    """Grava no OCI Object Storage com `if-none-match: *` (criação exclusiva)."""

    nome = "oci"

    def __init__(self, cliente, namespace: str):
        self._cliente = cliente
        self._namespace = namespace

    def salvar_json(self, bucket: str, nome_objeto: str, conteudo: dict) -> None:
        # Import local: o modo `local` não pode depender do pacote nem de credenciais OCI.
        from oci.exceptions import ServiceError

        corpo = _serializar(conteudo)
        try:
            self._cliente.put_object(
                self._namespace,
                bucket,
                nome_objeto,
                corpo,
                content_type="application/json",
                if_none_match="*",
            )
        except ServiceError as erro:
            if erro.status in (409, 412):
                raise ObjetoJaExiste(f"{bucket}/{nome_objeto}") from None
            raise _falha_servico(erro) from None
        except Exception as erro:
            raise _falha_comunicacao(erro) from None

    def apagar(self, bucket: str, nome_objeto: str) -> None:
        from oci.exceptions import ServiceError

        try:
            self._cliente.delete_object(self._namespace, bucket, nome_objeto)
        except ServiceError as erro:
            if erro.status == 404:  # já não existe: o resultado desejado
                return
            raise _falha_servico(erro) from None
        except Exception as erro:
            raise _falha_comunicacao(erro) from None


# ============================================================================
# NOMES DOS BUCKETS
# ============================================================================

@dataclass(frozen=True)
class NomesBuckets:
    recebidos: str
    urgentes: str
    rotina: str
    auditoria_humana: str
    rejeitados: str


def obter_buckets() -> NomesBuckets:
    """Monta os nomes a partir de OCI_BUCKET_PREFIXO (padrão `mediflow`), lido a cada chamada."""
    prefixo = os.getenv("OCI_BUCKET_PREFIXO") or "mediflow"
    return NomesBuckets(
        recebidos=f"{prefixo}-recebidos",
        urgentes=f"{prefixo}-urgentes",
        rotina=f"{prefixo}-rotina",
        auditoria_humana=f"{prefixo}-auditoria-humana",
        rejeitados=f"{prefixo}-rejeitados",
    )


# ============================================================================
# FÁBRICA
# ============================================================================

def _criar_repositorio_oci() -> RepositorioOCI:
    # Import local: só o modo `oci` precisa do SDK.
    import oci

    autenticacao = (os.getenv("OCI_AUTH") or "api_key").strip().lower()
    if autenticacao not in ("api_key", "instance_principal"):
        raise ValueError(
            f"OCI_AUTH inválido: {autenticacao!r}. Use 'api_key' ou 'instance_principal'."
        )

    try:
        if autenticacao == "api_key":
            config = oci.config.from_file(
                file_location=os.getenv("OCI_CONFIG_FILE") or oci.config.DEFAULT_LOCATION,
                profile_name=os.getenv("OCI_CONFIG_PROFILE") or "DEFAULT",
            )
            cliente = oci.object_storage.ObjectStorageClient(config)
        else:
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            cliente = oci.object_storage.ObjectStorageClient(config={}, signer=signer)

        namespace = os.getenv("OCI_NAMESPACE") or cliente.get_namespace().data
    except Exception as erro:
        raise FalhaArmazenamento(
            f"Não foi possível inicializar o cliente do Object Storage ({type(erro).__name__})."
        ) from None

    return RepositorioOCI(cliente, namespace)


def criar_repositorio() -> RepositorioDocumentos:
    """Escolhe o repositório por MEDIFLOW_ARMAZENAMENTO: `local` (padrão) ou `oci`."""
    modo = (os.getenv("MEDIFLOW_ARMAZENAMENTO") or "local").strip().lower()

    if modo == "local":
        return RepositorioLocal(
            Path(os.getenv("MEDIFLOW_ARMAZENAMENTO_LOCAL_DIR") or "armazenamento_local")
        )
    if modo == "oci":
        return _criar_repositorio_oci()

    raise ValueError(f"MEDIFLOW_ARMAZENAMENTO inválido: {modo!r}. Use 'local' ou 'oci'.")
