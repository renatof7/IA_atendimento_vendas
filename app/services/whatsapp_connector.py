"""
Conector Oficial WhatsApp Business Cloud API (Meta Graph API).
Responsabilidades (Documento 2, Seção 3):
1. Validação do Webhook da Meta (GET /webhook/whatsapp -> hub.challenge).
2. Recebimento e interpretação de mensagens (texto, botões interativos, transcrição/legenda de áudio e imagem).
3. Identificação automática do Canal de Origem, Campanha e UTM:
   - Click-to-WhatsApp Ads (Instagram Ads / Facebook Ads via objeto `referral`);
   - Placas físicas (QR Code ou link com código pré-preenchido da placa);
   - Botão de WhatsApp do Site (identificação da página ou empreendimento);
   - Contato direto no WhatsApp ("WhatsApp direto" quando não houver outro código).
4. Disparo de mensagens de texto livres (dentro da janela de 24h) e Modelos (Templates)
   aprovados pela Meta para follow-up após 24 horas.
"""

import json
import logging
import re
import urllib.request
from datetime import datetime
from typing import Optional

from app.config import settings

logger = logging.getLogger("lili.whatsapp_connector")


class WhatsAppCloudConnector:
    """Cliente e Parser para a API Oficial do WhatsApp Business (Meta)."""

    def __init__(self):
        self.outbox_logs: list[dict] = []

    @property
    def endpoint_messages(self) -> str:
        phone_id = settings.WHATSAPP_PHONE_NUMBER_ID or "PHONE_NUMBER_ID_MOCK"
        return f"https://graph.facebook.com/{settings.WHATSAPP_GRAPH_API_VERSION}/{phone_id}/messages"

    def validar_webhook_meta(
        self,
        hub_mode: Optional[str],
        hub_verify_token: Optional[str],
        hub_challenge: Optional[str],
    ) -> tuple[bool, str]:
        """Valida o desafio de assinatura do Webhook da Meta (GET /webhook/whatsapp)."""
        if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
            return True, hub_challenge or ""
        return False, "Token de verificação inválido"

    def identificar_origem_automatica(
        self,
        texto_mensagem: str,
        referral: Optional[dict] = None,
    ) -> tuple[str, Optional[str]]:
        """
        Identifica automaticamente o canal de origem e a campanha (Seção 3 do Documento 2):
        - Instagram Ads / Facebook Ads (via objeto `referral` da Meta Cloud API)
        - Placas físicas (QR Code com código de placa, ex: [PLACA-01] ou código da placa)
        - Site Oficial (botão do site citando página/empreendimento)
        - WhatsApp direto (quando não houver outro código)
        """
        if referral and isinstance(referral, dict):
            source_type = referral.get("source_type", "ad")
            headline = referral.get("headline") or referral.get("source_id") or "Campanha Meta Ads"
            ctwa_clid = referral.get("ctwa_clid")
            campanha = f"{headline} (ctwa_clid={ctwa_clid})" if ctwa_clid else headline
            return f"Meta Ads ({source_type})", campanha

        txt_lower = (texto_mensagem or "").lower()

        # Placas físicas (QR Code ou link com código da placa)
        m_placa = re.search(r"\[?placa[\s\-_:]*([a-z0-9\-]+)\]?", txt_lower)
        if m_placa:
            return "Placa física", f"Placa {m_placa.group(1).upper()}"

        # Botão do Site identificando página ou empreendimento
        if "vi no site" in txt_lower or "pelo site" in txt_lower or "[site" in txt_lower:
            return "Site Oficial", "Botão WhatsApp do Site"

        return "WhatsApp direto", None

    def extrair_evento_webhook(self, payload: dict) -> Optional[dict]:
        """
        Extrai telefone, nome do perfil, texto/mídia e metadados de origem de um payload
        padrão da WhatsApp Business Cloud API.
        """
        try:
            entries = payload.get("entry", [])
            if not entries:
                return None
            changes = entries[0].get("changes", [])
            if not changes:
                return None
            value = changes[0].get("value", {})
            messages = value.get("messages", [])
            if not messages:
                return None

            msg = messages[0]
            telefone = msg.get("from", "")
            msg_type = msg.get("type", "text")
            referral = msg.get("referral")

            contacts = value.get("contacts", [])
            nome_perfil = None
            if contacts:
                nome_perfil = contacts[0].get("profile", {}).get("name")

            if msg_type == "text":
                texto = msg.get("text", {}).get("body", "")
            elif msg_type == "interactive":
                inter = msg.get("interactive", {})
                texto = (
                    inter.get("button_reply", {}).get("title")
                    or inter.get("list_reply", {}).get("title")
                    or ""
                )
            elif msg_type == "audio":
                # Regra 3: Entender áudios enviados pelo lead e responder sempre em texto
                transcricao = msg.get("audio", {}).get("transcription") or "Olá, procuro um imóvel"
                texto = transcricao
            elif msg_type == "image":
                legenda = msg.get("image", {}).get("caption") or "Enviei uma imagem sobre o imóvel"
                texto = legenda
            else:
                texto = f"[{msg_type}]"

            origem, campanha = self.identificar_origem_automatica(texto, referral=referral)
            return {
                "message_id": msg.get("id"),
                "telefone": telefone,
                "nome_perfil_whatsapp": nome_perfil,
                "tipo_midia": msg_type,
                "texto": texto,
                "origem": origem,
                "campanha": campanha,
            }
        except Exception as exc:
            logger.warning(f"Erro ao interpretar payload do WhatsApp: {exc}")
            return None

    def enviar_mensagem_texto(self, telefone: str, texto: str) -> dict:
        """
        Envia mensagem de texto livre pelo WhatsApp (sempre em texto, mesmo quando o lead manda áudio).
        """
        payload_meta = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": telefone,
            "type": "text",
            "text": {"preview_url": True, "body": texto},
        }
        return self._disparar_graph_api(payload_meta)

    def enviar_template_meta(
        self,
        telefone: str,
        template_name: str,
        parametros_body: Optional[list[str]] = None,
        idioma: str = "pt_BR",
    ) -> dict:
        """
        Envia mensagem com modelo (Template) aprovado pela Meta (obrigatório após 24h sem resposta).
        """
        components = []
        if parametros_body:
            components.append(
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": p} for p in parametros_body],
                }
            )
        payload_meta = {
            "messaging_product": "whatsapp",
            "to": telefone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": idioma},
                "components": components,
            },
        }
        return self._disparar_graph_api(payload_meta)

    def _disparar_graph_api(self, payload: dict) -> dict:
        """Executa o POST para a Graph API da Meta (ou registra em modo simulação se sem token)."""
        registro_log = {
            "timestamp": datetime.now().isoformat(),
            "endpoint": self.endpoint_messages,
            "payload": payload,
            "modo": "producao" if settings.WHATSAPP_ACCESS_TOKEN else "simulacao_dry_run",
        }

        if settings.WHATSAPP_ACCESS_TOKEN and settings.WHATSAPP_PHONE_NUMBER_ID:
            try:
                req = urllib.request.Request(
                    self.endpoint_messages,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
                        "Content-Type": "application/json",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    resposta_api = json.loads(resp.read().decode("utf-8"))
                registro_log["status_http"] = 200
                registro_log["resposta_meta"] = resposta_api
            except Exception as exc:
                registro_log["status_http"] = 500
                registro_log["erro"] = str(exc)
        else:
            registro_log["status_http"] = 200
            registro_log["resposta_meta"] = {
                "messaging_product": "whatsapp",
                "contacts": [{"input": payload.get("to"), "wa_id": payload.get("to")}],
                "messages": [{"id": f"wamid.SIMULADO_{len(self.outbox_logs) + 1}"}],
            }

        self.outbox_logs.append(registro_log)
        return registro_log
