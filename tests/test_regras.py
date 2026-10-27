"""
MediFlow - Teste Unitário dos 3 Cenários Oficiais
Hackathon ONE G10 - Grupo 10: MediFlow

Responsável: Lethicia
Mapeamento: tests/test_regras.py
Execução: python -m unittest tests/test_regras.py
"""

import json
import os
import unittest

from contratos.modelos import (
    DocumentoEntrada,
    TriagemResposta,
    ClassificacaoDocumento,
    DadosExtraidos,
    DestinoRoteamento
)
from regras.regras_clinicas import executar_roteamento_clinico

class TestMediFlowCenarios(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Localiza a raiz do projeto (um nível acima da pasta tests)
        cls.raiz_projeto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.pasta_dados = os.path.join(cls.raiz_projeto, "dados_teste")

    def test_cenario_1_rotina(self):
        """Cenário 1: Laudo de rotina ambulatorial deve ir para Prontuário sem auditoria."""
        caminho = os.path.join(self.pasta_dados, "1_rotina", "exemplo.json")
        with open(caminho, "r", encoding="utf-8") as f:
            dado = json.load(f)

        req = DocumentoEntrada(**dado["requisicao_entrada"])
        classif = ClassificacaoDocumento(**dado["resposta_esperada"]["classificacao"])
        dados_ext = DadosExtraidos(**dado["resposta_esperada"]["dados_extraidos"])

        decisao = executar_roteamento_clinico(classif, dados_ext, req.documento_texto, req.canal_origem)

        self.assertEqual(decisao.destino_principal, DestinoRoteamento.PRONTUARIO_ELETRONICO)
        self.assertFalse(decisao.requer_auditoria_humana)

    def test_cenario_2_urgencia(self):
        """Cenário 2: TEP Agudo deve ir para Fila de Emergência com alerta gerado."""
        caminho = os.path.join(self.pasta_dados, "2_urgencia", "exemplo.json")
        with open(caminho, "r", encoding="utf-8") as f:
            dado = json.load(f)

        req = DocumentoEntrada(**dado["requisicao_entrada"])
        classif = ClassificacaoDocumento(**dado["resposta_esperada"]["classificacao"])
        dados_ext = DadosExtraidos(**dado["resposta_esperada"]["dados_extraidos"])

        decisao = executar_roteamento_clinico(classif, dados_ext, req.documento_texto, req.canal_origem)

        self.assertEqual(decisao.destino_principal, DestinoRoteamento.FILA_EMERGENCIA)
        self.assertIsNotNone(decisao.notificacao_gerada)
        self.assertIn("TEP", decisao.notificacao_gerada.mensagem)

    def test_cenario_3_auditoria_humana(self):
        """Cenário 3: Receituário com rasura/ilegível deve ir para Human-in-the-Loop."""
        caminho = os.path.join(self.pasta_dados, "3_auditoria_humana", "exemplo.json")
        with open(caminho, "r", encoding="utf-8") as f:
            dado = json.load(f)

        req = DocumentoEntrada(**dado["requisicao_entrada"])
        classif = ClassificacaoDocumento(**dado["resposta_esperada"]["classificacao"])
        dados_ext = DadosExtraidos(**dado["resposta_esperada"]["dados_extraidos"])

        decisao = executar_roteamento_clinico(classif, dados_ext, req.documento_texto, req.canal_origem)

        self.assertEqual(decisao.destino_principal, DestinoRoteamento.FILA_REVISAO_HUMANA)
        self.assertTrue(decisao.requer_auditoria_humana)

if __name__ == "__main__":
    unittest.main()
