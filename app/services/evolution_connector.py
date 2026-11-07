"""
Conector WhatsApp Gateway Não-Oficial via Evolution API (v2 / v1).
Conexão simples via leitura de QR Code no celular (WhatsApp Business).
Dispensa APIs da Meta e burocracia de verificação de empresa.

Responsabilidades:
1. Recebimento e normalização de webhooks da Evolution API (evento 'messages.upsert').
2. Detecção automática de origem (Placas, Site, Ads, WhatsApp Direto).
3. Envio de mensagens de texto com formatação natural e simulação de presença ('digitando...').
4. Consulta e retorno do QR Code em tempo real (base64) para o painel web.
5. Modo de simulação automático (dry-run) quando o servidor da Evolution API estiver offline.
"""

import json
import logging
import re
import urllib.request
import urllib.error
from datetime import datetime
from typing import Optional

from app.config import settings

logger = logging.getLogger("lili.evolution_connector")


class EvolutionAPIConnector:
    """Cliente e Webhook Handler para a Evolution API (WhatsApp QR Code)."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        instance_name: Optional[str] = None,
    ):
        self.api_url = (api_url or settings.EVOLUTION_API_URL).rstrip("/")
        self.api_key = api_key or settings.EVOLUTION_API_KEY
        self.instance_name = instance_name or settings.EVOLUTION_INSTANCE_NAME
        self.outbox_logs: list[dict] = []

    def _headers(self) -> dict:
        return {
            "apikey": self.api_key,
            "Content-Type": "application/json",
        }

    def _http_request(self, endpoint: str, method: str = "GET", data: Optional[dict] = None) -> tuple[int, dict]:
        """Executa chamada HTTP à Evolution API com tratamento de erros."""
        url = f"{self.api_url}{endpoint}"
        body = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=body, headers=self._headers(), method=method)
        try:
            with urllib.request.urlopen(req, timeout=6) as resp:
                status = resp.status
                raw = resp.read().decode("utf-8")
                return status, json.loads(raw) if raw else {}
        except urllib.error.HTTPError as he:
            try:
                raw_err = he.read().decode("utf-8")
                return he.code, json.loads(raw_err) if raw_err else {"erro": str(he)}
            except Exception:
                return he.code, {"erro": str(he)}
        except Exception as exc:
            return 503, {"erro": f"Servidor Evolution API offline ou inacessível: {exc}"}

    def verificar_estado_conexao(self) -> dict:
        """Verifica se a instância da Evolution API está conectada ao WhatsApp."""
        status_code, dados = self._http_request(f"/instance/connectionState/{self.instance_name}")
        if status_code == 200:
            inst = dados.get("instance", {})
            state = inst.get("state") or dados.get("state", "close")
            return {
                "conectado": state == "open",
                "estado": state,
                "instancia": self.instance_name,
                "detalhes": dados,
            }
        return {
            "conectado": False,
            "estado": "offline" if status_code == 503 else "desconectado",
            "instancia": self.instance_name,
            "detalhes": dados,
        }

    def criar_ou_obter_instancia(self) -> tuple[int, dict]:
        """Cria a instância na Evolution API se ela ainda não existir."""
        payload_create = {
            "instanceName": self.instance_name,
            "token": self.api_key,
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS",
        }
        return self._http_request("/instance/create", method="POST", data=payload_create)

    def obter_qrcode(self) -> dict:
        """
        Obtém o QR Code em Base64 ou código de pareamento para conectar o WhatsApp no painel.
        Cria a instância automaticamente na Evolution API se ela ainda não existir.
        """
        # 1. Tenta criar a instância (se for a primeira conexão)
        status_create, dados_create = self.criar_ou_obter_instancia()

        # Se o servidor Evolution estiver offline
        if status_create == 503:
            return {
                "sucesso": False,
                "erro": "Servidor da Evolution API offline na porta 8080. Verifique se o Docker está em execução com 'docker compose up -d'.",
                "detalhes": dados_create,
            }

        # Se a criação já devolveu o QR Code diretamente:
        base64_qr = None
        code = None
        if status_create in (200, 201) and isinstance(dados_create, dict):
            base64_qr = (
                dados_create.get("base64")
                or dados_create.get("qrcode", {}).get("base64")
                or (dados_create.get("qrcode") if isinstance(dados_create.get("qrcode"), str) and "base64" in dados_create.get("qrcode") else None)
            )
            code = (
                dados_create.get("code")
                or dados_create.get("pairingCode")
                or dados_create.get("qrcode", {}).get("code")
                or dados_create.get("qrcode", {}).get("pairingCode")
            )

        # 2. Se a instância já existia ou precisa de um novo QR Code, chama /instance/connect
        status_connect = None
        dados_connect = None
        if not base64_qr:
            status_connect, dados_connect = self._http_request(f"/instance/connect/{self.instance_name}")
            if status_connect in (200, 201) and isinstance(dados_connect, dict):
                base64_qr = (
                    dados_connect.get("base64")
                    or dados_connect.get("qrcode", {}).get("base64")
                    or (dados_connect.get("qrcode") if isinstance(dados_connect.get("qrcode"), str) and "base64" in dados_connect.get("qrcode") else None)
                )
                code = (
                    dados_connect.get("code")
                    or dados_connect.get("pairingCode")
                    or dados_connect.get("qrcode", {}).get("code")
                    or dados_connect.get("qrcode", {}).get("pairingCode")
                )
                # Verifica se a instância já está conectada
                inst_state = dados_connect.get("instance", {}).get("state") or dados_connect.get("state")
                if inst_state == "open":
                    return {
                        "sucesso": True,
                        "ja_conectado": True,
                        "mensagem": "WhatsApp já está conectado com sucesso!",
                        "instancia": self.instance_name,
                    }

        if base64_qr:
            if not base64_qr.startswith("data:image"):
                base64_qr = f"data:image/png;base64,{base64_qr}"
            return {
                "sucesso": True,
                "qrcode_base64": base64_qr,
                "pairing_code": code,
                "instancia": self.instance_name,
            }

        # Diagnóstico detalhado de erro
        erro_desc = "Não foi possível obter o QR Code."
        if dados_connect and isinstance(dados_connect, dict):
            erro_desc = dados_connect.get("erro") or dados_connect.get("message") or dados_connect.get("error") or erro_desc
        elif dados_create and isinstance(dados_create, dict):
            erro_desc = dados_create.get("erro") or dados_create.get("message") or dados_create.get("error") or erro_desc

        return {
            "sucesso": False,
            "erro": str(erro_desc),
            "detalhes": {
                "status_create": status_create,
                "dados_create": dados_create,
                "status_connect": status_connect,
                "dados_connect": dados_connect,
            },
        }

    def identificar_origem_automatica(self, texto_mensagem: str) -> tuple[str, Optional[str]]:
        """
        Identifica automaticamente o canal de origem e a campanha a partir da mensagem:
        - Placas físicas (QR Code com código, ex: [PLACA-01] ou código de obra)
        - Botão do Site (identificação da página ou empreendimento)
        - WhatsApp direto (quando não houver tag)
        """
        txt_lower = (texto_mensagem or "").lower()

        # Placas físicas (QR Code ou link pré-formatado da placa)
        m_placa = re.search(r"\[?placa[\s\-_:]*([a-z0-9\-]+)\]?", txt_lower)
        if m_placa:
            return "Placa física", f"Placa {m_placa.group(1).upper()}"

        # Botão do Site identificando página ou empreendimento
        if "vi no site" in txt_lower or "pelo site" in txt_lower or "[site" in txt_lower:
            return "Site Oficial", "Botão WhatsApp do Site"

        # Instagram / Facebook Ads orgânico via mensagem prévia
        if "anúncio" in txt_lower or "anuncio" in txt_lower or "instagram" in txt_lower:
            return "Instagram Ads", "Campanha MCMV"

        return "WhatsApp direto", None

    def extrair_evento_webhook(self, payload: dict) -> Optional[dict]:
        """
        Extrai e normaliza mensagens recebidas do webhook da Evolution API (v1 e v2).
        Ignora mensagens enviadas pelo próprio robô ('fromMe': True) e grupos.
        """
        try:
            event = payload.get("event") or payload.get("type", "")
            # Suporta eventos messages.upsert e variações
            data = payload.get("data") or payload
            if not isinstance(data, dict):
                return None

            key = data.get("key", {})
            # Ignora mensagens enviadas pelo próprio bot
            if key.get("fromMe", False):
                return None

            remote_jid = key.get("remoteJid", "")
            if not remote_jid or "@g.us" in remote_jid or "status@broadcast" in remote_jid:
                # Ignora grupos e status broadcast
                return None

            # Normaliza telefone: extrai somente dígitos (ex: 5548999998888)
            telefone = re.sub(r"\D", "", remote_jid.split("@")[0])
            if not telefone:
                return None

            push_name = data.get("pushName")
            msg_obj = data.get("message") or {}

            # Extração de texto de múltiplos formatos de mensagem do WhatsApp
            texto = ""
            tipo_midia = "text"
            if "conversation" in msg_obj:
                texto = msg_obj["conversation"]
            elif "extendedTextMessage" in msg_obj:
                texto = msg_obj["extendedTextMessage"].get("text", "")
            elif "audioMessage" in msg_obj:
                tipo_midia = "audio"
                texto = msg_obj["audioMessage"].get("caption") or "Olá, procuro um imóvel"
            elif "imageMessage" in msg_obj:
                tipo_midia = "image"
                texto = msg_obj["imageMessage"].get("caption") or "Enviei uma foto do imóvel"
            elif "buttonsResponseMessage" in msg_obj:
                texto = msg_obj["buttonsResponseMessage"].get("selectedDisplayText", "")
            elif "listResponseMessage" in msg_obj:
                texto = msg_obj["listResponseMessage"].get("title", "")
            else:
                texto = str(msg_obj.get("text", ""))

            if not texto:
                return None

            origem, campanha = self.identificar_origem_automatica(texto)
            return {
                "message_id": key.get("id"),
                "telefone": telefone,
                "nome_perfil_whatsapp": push_name,
                "tipo_midia": tipo_midia,
                "texto": texto.strip(),
                "origem": origem,
                "campanha": campanha,
            }
        except Exception as exc:
            logger.warning(f"Erro ao processar payload da Evolution API: {exc}")
            return None

    def enviar_presenca_digitando(self, telefone: str, delay_ms: int = 1200) -> dict:
        """Envia status 'digitando...' (composing) para deixar a resposta mais humana."""
        tel_limpo = re.sub(r"\D", "", telefone)
        payload = {
            "number": tel_limpo,
            "presence": "composing",
            "delay": delay_ms,
        }
        status, resp = self._http_request(f"/chat/sendPresence/{self.instance_name}", method="POST", data=payload)
        return {"status_http": status, "resposta": resp}

    def enviar_mensagem_texto(self, telefone: str, texto: str) -> dict:
        """
        Envia mensagem de texto para o WhatsApp via Evolution API.
        Se a Evolution API estiver offline, registra em modo simulação no log de saída.
        """
        tel_limpo = re.sub(r"\D", "", telefone)
        payload = {
            "number": tel_limpo,
            "text": texto,
            "delay": 1200,
        }

        endpoint = f"/message/sendText/{self.instance_name}"
        status_code, resposta_api = self._http_request(endpoint, method="POST", data=payload)

        registro_log = {
            "timestamp": datetime.now().isoformat(),
            "provedor": "evolution_api",
            "instancia": self.instance_name,
            "endpoint": f"{self.api_url}{endpoint}",
            "telefone": tel_limpo,
            "texto": texto,
            "status_http": status_code,
            "resposta_evolution": resposta_api,
            "modo": "producao" if status_code in (200, 201) else "simulacao_dry_run",
        }

        self.outbox_logs.append(registro_log)
        return registro_log
