"""Esquemas de saída de referência para a interface.

O contrato definitivo precisa ser alinhado com a pessoa responsável pela validação Pydantic.
"""
from typing import Any
from pydantic import BaseModel, Field


class Classificacao(BaseModel):
    tipo_documento: str = "indeterminado"
    especialidade: str | None = None
    nivel_prioridade: str = "Revisao_Humana"
    score_confianca_classificacao: float = Field(default=0.0, ge=0.0, le=1.0)


class DecisaoRoteamento(BaseModel):
    destino_principal: str = "Fila_Revisao_Humana"
    requer_auditoria_humana: bool = True
    justificativa_roteamento: str = "Resultado não validado; requer revisão humana."


class ResultadoTriagem(BaseModel):
    status: str = "revisao_humana"
    documento_id: str
    classificacao: Classificacao = Field(default_factory=Classificacao)
    dados_extraidos: dict[str, Any] = Field(default_factory=dict)
    decisao_roteamento: DecisaoRoteamento = Field(default_factory=DecisaoRoteamento)
