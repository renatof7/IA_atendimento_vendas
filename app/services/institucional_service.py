"""
Serviço de Base de Conhecimento Institucional, Plantões, Documentação, Canais de
Encaminhamento e Perguntas Frequentes (FAQ) da Construtora Demo.
"""

import json
from pathlib import Path
from typing import Optional

from app.config import BASE_DIR
from app.domain.mcmv import _normalizar_texto

INSTITUCIONAL_JSON_PATH = BASE_DIR / "data" / "base_institucional.json"


class ServicoInstitucional:
    """Consulta a base institucional oficial da construtora."""

    def __init__(self, json_path: Optional[Path] = None):
        self.json_path: Path = json_path or INSTITUCIONAL_JSON_PATH
        self._dados: dict = {}
        self.recarregar()

    def recarregar(self) -> dict:
        if self.json_path.exists():
            self._dados = json.loads(self.json_path.read_text(encoding="utf-8"))
        return self._dados

    @property
    def dados(self) -> dict:
        if not self._dados:
            self.recarregar()
        return self._dados

    def salvar(self, novos_dados: dict) -> dict:
        """Salva alterações na base institucional JSON e recarrega em memória."""
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        self.json_path.write_text(
            json.dumps(novos_dados, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self._dados = novos_dados
        return {"status": "salvo", "dados": self._dados}

    def consultar_topico(self, topico: str, cidade: Optional[str] = None) -> dict:
        """
        Retorna as informações institucionais filtradas por tópico:
        - 'plantao' / 'horarios' / 'endereco'
        - 'documentacao'
        - 'pos_venda' / 'assistencia' / 'boleto'
        - 'parcerias' / 'corretor'
        - 'fornecedor' / 'curriculo' / 'imprensa'
        - 'diferenciais' / 'construtora'
        - 'faq' / geral
        """
        t_norm = _normalizar_texto(topico)
        d = self.dados

        if any(k in t_norm for k in ("plantao", "stand", "horario", "endereco", "onde fica")):
            stands = d.get("horarios_e_plantoes", {}).get("stands", [])
            if cidade:
                c_norm = _normalizar_texto(cidade)
                filtrados = [s for s in stands if c_norm in _normalizar_texto(s.get("cidade", ""))]
                if filtrados:
                    stands = filtrados
            return {
                "topico": "horarios_e_plantoes",
                "horario_atendimento_humano": d.get("horarios_e_plantoes", {}).get("horario_atendimento_humano"),
                "stands": stands,
            }

        if any(k in t_norm for k in ("documento", "documentacao", "rg", "holerite", "levar")):
            return {
                "topico": "documentacao_basica_simulacao",
                "dados": d.get("documentacao_basica_simulacao", {}),
            }

        if any(k in t_norm for k in ("pos_venda", "pos-venda", "boleto", "assistencia", "chave", "ja comprei")):
            return {
                "topico": "pos_venda_assistencia_boleto",
                "dados": d.get("canais_encaminhamento_especifico", {}).get("pos_venda_assistencia_boleto", {}),
            }

        if any(k in t_norm for k in ("parceria", "corretor", "imobiliaria")):
            return {
                "topico": "parcerias_corretores_imobiliarias",
                "dados": d.get("canais_encaminhamento_especifico", {}).get("parcerias_corretores_imobiliarias", {}),
            }

        if any(k in t_norm for k in ("fornecedor", "curriculo", "vaga", "imprensa", "rh", "compras")):
            return {
                "topico": "fornecedores_imprensa_curriculos",
                "dados": d.get("canais_encaminhamento_especifico", {}).get("fornecedores_imprensa_curriculos", {}),
            }

        if any(k in t_norm for k in ("diferencia", "construtora", "sobre")):
            return {
                "topico": "construtora_e_diferenciais",
                "dados": d.get("construtora", {}),
            }

        return {
            "topico": "institucional_completo",
            "dados": d,
        }
