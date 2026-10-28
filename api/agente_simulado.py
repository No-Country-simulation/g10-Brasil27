"""
MediFlow - Agente Simulado (substituto temporário do grafo de decisão)
Hackathon ONE G10 - Grupo 10: MediFlow

Mapeamento: api/agente_simulado.py
O grafo de decisão com LLM (agente/, responsabilidade da Ingrid) ainda não existe.
Este módulo faz o papel dele com a MESMA assinatura que o grafo deve expor:

    analisar_documento(entrada: DocumentoEntrada) -> tuple[ClassificacaoDocumento, DadosExtraidos]

Quando o grafo existir, basta trocar o import em api/triagem.py.

Como funciona: se o texto do documento (normalizado) for igual ao de um dos 3 cenários
de dados_teste/, devolve a classificação e os dados extraídos daquele cenário. Qualquer
outro documento, inclusive o que chega só em Base64, volta como "não identificado" com
confiança 0.0, o que as regras da Lethicia encaminham para a revisão humana.
"""

import json
from functools import lru_cache
from pathlib import Path

from contratos.modelos import (
    ClassificacaoDocumento,
    DadosExtraidos,
    DocumentoEntrada,
    TipoDocumento,
)

# Resolvido a partir deste arquivo, não do diretório de execução.
PASTA_DADOS_TESTE = Path(__file__).resolve().parent.parent / "dados_teste"


def _normalizar(texto: str) -> str:
    return " ".join(texto.split())


@lru_cache(maxsize=1)
def _carregar_cenarios() -> dict[str, tuple[ClassificacaoDocumento, DadosExtraidos]]:
    cenarios = {}
    for arquivo in sorted(PASTA_DADOS_TESTE.glob("*/exemplo.json")):
        with open(arquivo, encoding="utf-8") as f:
            dado = json.load(f)
        texto = dado["requisicao_entrada"]["documento_texto"]
        esperada = dado["resposta_esperada"]
        cenarios[_normalizar(texto)] = (
            ClassificacaoDocumento(**esperada["classificacao"]),
            DadosExtraidos(**esperada["dados_extraidos"]),
        )
    return cenarios


def analisar_documento(entrada: DocumentoEntrada) -> tuple[ClassificacaoDocumento, DadosExtraidos]:
    """Classifica e extrai os dados do documento (versão simulada, ver o docstring do módulo)."""
    if entrada.documento_texto:
        encontrado = _carregar_cenarios().get(_normalizar(entrada.documento_texto))
        if encontrado is not None:
            classificacao, dados = encontrado
            # Cópias: quem receber o resultado não pode alterar os cenários em cache.
            return classificacao.model_copy(deep=True), dados.model_copy(deep=True)

    return (
        ClassificacaoDocumento(
            tipo_documento=TipoDocumento.OUTRO_DESCONHECIDO.value,
            especialidade=None,
            score_confianca_classificacao=0.0,
        ),
        DadosExtraidos(),
    )
