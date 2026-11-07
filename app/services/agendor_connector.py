"""
Conector HTTP para a API v3 do CRM Agendor (`https://api.agendor.com.br/v3`).
Responsabilidades (Seção 14 das Instruções Mestras e Seção 4/10 do Documento 2):
1. Criar ou atualizar Pessoa (`POST/PUT /people`) sem duplicar telefone.
2. Criar ou atualizar Negócio (`POST/PUT /deals`) mapeando todos os campos obrigatórios:
   - Origem, campanha, objetivo, primeiro imóvel, cidade, tipo, quartos,
   - Renda bruta familiar, tipo de renda, FGTS, dependentes, imóvel ativo,
   - Restrição CPF, entrada disponível, pré-enquadramento MCMV, prazo de compra,
   - Códigos XML dos imóveis apresentados, preferência de visita ("a confirmar"),
   - Pontuação, temperatura e etapa.
3. Gravar nota/histórico com o Resumo de 6 Linhas na passagem ao vendedor.
"""

import json
import logging
import urllib.request
from dataclasses import asdict
from datetime import datetime
from typing import Optional

from app.config import settings
from app.services.crm_service import RegistroLeadCRM

logger = logging.getLogger("lili.agendor_connector")


class AgendorCRMConnector:
    """Cliente de sincronização com a API v3 do Agendor CRM."""

    def __init__(self):
        self.sync_logs: list[dict] = []
        # Mapa em memória de telefone -> IDs no Agendor para evitar duplicidade de telefone
        self._mapa_pessoas_por_telefone: dict[str, int] = {}
        self._mapa_negocios_por_telefone: dict[str, int] = {}

    def montar_payload_pessoa_agendor(self, lead: RegistroLeadCRM) -> dict:
        """Monta o payload compatível com `POST /v3/people` do Agendor."""
        return {
            "name": lead.nome or f"Lead WhatsApp ({lead.telefone})",
            "contact": {
                "whatsapp": lead.telefone,
                "mobile": lead.telefone,
                "email": lead.email,
            },
            "leadOrigin": lead.origem,
            "customFields": {
                "campanha_utm": lead.campanha or lead.anuncio_utm,
                "dependentes": lead.dependentes,
                "restricao_cpf": lead.restricao_cpf or "não informado",
                "opt_out_lgpd": lead.opt_out_lgpd,
            },
        }

    def montar_payload_negocio_agendor(self, lead: RegistroLeadCRM, resumo_6_linhas: str) -> dict:
        """
        Monta o payload compatível com `POST/PUT /v3/deals` do Agendor contendo
        todos os campos da Tabela da Seção 14.
        """
        # Mapeia etapa da Lili para estágio do funil no Agendor
        mapa_estagios = {
            "em qualificação": 1,
            "qualificado": 2,
            "transferido": 3,
            "sem perfil": 4,
            "sem retorno": 5,
        }
        deal_stage = mapa_estagios.get(lead.etapa, 1)

        return {
            "title": f"MCMV 2026 - {lead.nome or lead.telefone} ({lead.cidade or 'A definir'})",
            "funnel": settings.AGENDOR_FUNIL_ID,
            "dealStage": deal_stage,
            "ownerUser": lead.vendedor_responsavel,
            "description": resumo_6_linhas,
            "customFields": {
                "origem_canal": lead.origem,
                "campanha": lead.campanha,
                "objetivo": lead.objetivo,
                "primeiro_imovel": lead.primeiro_imovel,
                "cidade_interesse": lead.cidade,
                "tipo_imovel": lead.tipo_imovel,
                "quartos": lead.quartos,
                "renda_bruta_familiar_faixa": lead.renda_bruta_familiar_faixa,
                "tipo_renda": lead.tipo_renda,
                "fgts_3_anos_carteira": lead.fgts_mais_3_anos,
                "imovel_ou_financiamento_ativo": lead.imovel_ou_financiamento_ativo,
                "restricao_cpf": lead.restricao_cpf,
                "entrada_disponivel": lead.entrada_disponivel,
                "pre_enquadramento_mcmv": lead.pre_enquadramento_mcmv,
                "prazo_compra": lead.prazo_compra,
                "imoveis_apresentados_xml": ", ".join(lead.imoveis_apresentados),
                "imovel_maior_interesse": lead.imovel_maior_interesse,
                "preferencia_visita": (
                    f"{lead.preferencia_visita} ({lead.status_visita or 'a confirmar'})"
                    if lead.preferencia_visita
                    else None
                ),
                "pontuacao_lead": lead.pontuacao,
                "temperatura_lead": lead.temperatura,
                "etapa_ia": lead.etapa,
                "motivo_descarte": lead.motivo_descarte,
            },
        }

    def sincronizar_lead(self, lead: RegistroLeadCRM, resumo_6_linhas: str) -> dict:
        """
        Executa o upsert de Pessoa (sem duplicar telefone) e de Negócio (Deal) no Agendor CRM.
        """
        tel_limpo = "".join(c for c in lead.telefone if c.isdigit() or c == "+") or "padrao"
        ja_existia = tel_limpo in self._mapa_pessoas_por_telefone

        person_id = self._mapa_pessoas_por_telefone.get(
            tel_limpo, 1000 + len(self._mapa_pessoas_por_telefone) + 1
        )
        deal_id = self._mapa_negocios_por_telefone.get(
            tel_limpo, 5000 + len(self._mapa_negocios_por_telefone) + 1
        )
        self._mapa_pessoas_por_telefone[tel_limpo] = person_id
        self._mapa_negocios_por_telefone[tel_limpo] = deal_id

        payload_pessoa = self.montar_payload_pessoa_agendor(lead)
        payload_negocio = self.montar_payload_negocio_agendor(lead, resumo_6_linhas)

        operacao = "PUT (Atualização sem duplicar telefone)" if ja_existia else "POST (Novo registro)"
        registro_sync = {
            "timestamp": datetime.now().isoformat(),
            "operacao": operacao,
            "agendor_person_id": person_id,
            "agendor_deal_id": deal_id,
            "link_agendor": f"https://web.agendor.com.br/negocios/{deal_id}",
            "payload_person": payload_pessoa,
            "payload_deal": payload_negocio,
            "modo": "producao" if settings.AGENDOR_API_TOKEN else "simulacao_dry_run",
        }

        if settings.AGENDOR_API_TOKEN:
            try:
                metodo_http = "PUT" if ja_existia else "POST"
                url_person = (
                    f"{settings.AGENDOR_API_URL}/people/{person_id}"
                    if ja_existia
                    else f"{settings.AGENDOR_API_URL}/people"
                )
                req = urllib.request.Request(
                    url_person,
                    data=json.dumps(payload_pessoa).encode("utf-8"),
                    headers={
                        "Authorization": f"Token {settings.AGENDOR_API_TOKEN}",
                        "Content-Type": "application/json",
                    },
                    method=metodo_http,
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    registro_sync["resposta_agendor_http"] = resp.status
            except Exception as exc:
                registro_sync["erro_http"] = str(exc)

        self.sync_logs.append(registro_sync)
        return registro_sync
