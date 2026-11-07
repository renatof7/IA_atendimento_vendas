"""
Inicializador do Console Web e API da Lili IA na porta 8000.
Funciona imediatamente mesmo sem pacotes externos instalados (via ThreadingHTTPServer nativo)
ou via Uvicorn/FastAPI quando instalado.
"""

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from app.agent.engine import MotorLili
from app.services.followup_service import MotorFollowUpENutricao
from app.services.whatsapp_connector import WhatsAppCloudConnector
from app.services.evolution_connector import EvolutionAPIConnector
from app.domain.mcmv import calcular_pre_enquadramento
from app.config import settings, BASE_DIR
from app.web_ui import WEB_CONSOLE_HTML

motor_lili = MotorLili()
motor_followup = MotorFollowUpENutricao(crm=motor_lili.crm, catalogo=motor_lili.catalogo)
whatsapp_api = WhatsAppCloudConnector()
evolution_api = EvolutionAPIConnector()


class LiliHTTPHandler(BaseHTTPRequestHandler):
    """Servidor HTTP nativo compatível com todas as rotas da API FastAPI da Lili."""

    def log_message(self, format: str, *args) -> None:
        # Log conciso de requisições
        print(f"[Lili HTTP] {self.command} {self.path} -> {args[1] if len(args) > 1 else ''}")

    def _enviar_json(self, dados: dict, status: int = 200) -> None:
        corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def _enviar_html(self, html: str, status: int = 200) -> None:
        corpo = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(corpo)

    def _ler_body_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        try:
            return json.loads(raw)
        except Exception:
            return {}

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        rota = parsed.path

        if rota == "/":
            import importlib
            import app.web_ui
            importlib.reload(app.web_ui)
            self._enviar_html(app.web_ui.WEB_CONSOLE_HTML)
            return

        if rota == "/webhook/whatsapp":
            qs = parse_qs(parsed.query)
            ok, challenge = whatsapp_api.validar_webhook_meta(
                qs.get("hub.mode", [None])[0],
                qs.get("hub.verify_token", [None])[0],
                qs.get("hub.challenge", [None])[0],
            )
            corpo = challenge.encode("utf-8")
            self.send_response(200 if ok else 403)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)
            return

        if rota == "/api/evolution/status":
            self._enviar_json(evolution_api.verificar_estado_conexao())
            return

        if rota == "/api/evolution/qrcode":
            self._enviar_json(evolution_api.obter_qrcode())
            return

        if rota == "/api/integracoes/logs":
            self._enviar_json(
                {
                    "evolution_api_outbox": evolution_api.outbox_logs[-10:],
                    "whatsapp_cloud_api_outbox": whatsapp_api.outbox_logs[-10:],
                    "agendor_crm_v3_sync": motor_lili.crm.agendor_api.sync_logs[-10:],
                }
            )
            return

        if rota == "/api/kb":
            xml_txt = (
                settings.XML_IMOVEIS_PATH.read_text(encoding="utf-8")
                if settings.XML_IMOVEIS_PATH.exists()
                else ""
            )
            self._enviar_json(
                {
                    "institucional": motor_lili.institucional.dados,
                    "xml_imoveis": xml_txt,
                    "system_prompt": motor_lili.system_prompt,
                }
            )
            return

        if rota == "/api/leads":
            self._enviar_json({"leads": motor_lili.crm.listar_todos_leads()})
            return

        m_lead = re.fullmatch(r"/api/leads/([^/]+)", rota)
        if m_lead:
            tel = m_lead.group(1)
            lead = motor_lili.crm.obter_ou_criar_lead(tel)
            resumo = motor_lili.crm.gerar_resumo_6_linhas(lead)
            self._enviar_json(
                {
                    "lead": lead.__dict__,
                    "resumo_6_linhas_preview": resumo,
                    "alertas_gestor": motor_followup.alertas_gestor[-5:],
                }
            )
            return

        if rota == "/api/imoveis/admin":
            self._enviar_json({"imoveis": motor_lili.catalogo.listar_todos_admin()})
            return

        if rota == "/api/imoveis":
            qs = parse_qs(parsed.query)
            quartos_str = qs.get("quartos", [None])[0]
            res = motor_lili.catalogo.buscar_imoveis(
                cidade=qs.get("cidade", [None])[0],
                bairro=qs.get("bairro", [None])[0],
                tipo=qs.get("tipo", [None])[0],
                quartos=int(quartos_str) if quartos_str and quartos_str.isdigit() else None,
                faixa_mcmv=qs.get("faixa_mcmv", [None])[0],
            )
            self._enviar_json(res)
            return

        self._enviar_json({"erro": "Rota não encontrada"}, status=404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        rota = parsed.path
        body = self._ler_body_json()

        if rota == "/api/chat":
            res = motor_lili.processar_mensagem(
                telefone=body.get("telefone", "5548999990001"),
                mensagem=body.get("mensagem", ""),
                origem=body.get("origem", "Instagram Ads"),
                campanha=body.get("campanha", "MCMV_2026_SairDoAluguel"),
            )
            if res.get("resposta_lili"):
                if settings.WHATSAPP_PROVIDER == "evolution":
                    evolution_api.enviar_mensagem_texto(
                        telefone=body.get("telefone", "5548999990001"),
                        texto=res["resposta_lili"],
                    )
                else:
                    whatsapp_api.enviar_mensagem_texto(
                        telefone=body.get("telefone", "5548999990001"),
                        texto=res["resposta_lili"],
                    )
            self._enviar_json(res)
            return

        if rota == "/webhook/evolution":
            evento = evolution_api.extrair_evento_webhook(body)
            if not evento:
                self._enviar_json({"status": "ignorado_sem_mensagem"})
                return
            if evento.get("nome_perfil_whatsapp"):
                lead_ex = motor_lili.crm.obter_ou_criar_lead(evento["telefone"])
                if not lead_ex.nome:
                    motor_lili.crm.atualizar_lead(evento["telefone"], nome=evento["nome_perfil_whatsapp"])
            evolution_api.enviar_presenca_digitando(evento["telefone"], delay_ms=1200)
            res = motor_lili.processar_mensagem(
                telefone=evento["telefone"],
                mensagem=evento["texto"],
                origem=evento["origem"],
                campanha=evento["campanha"],
            )
            envio_wa = None
            if res.get("resposta_lili"):
                envio_wa = evolution_api.enviar_mensagem_texto(evento["telefone"], res["resposta_lili"])
            self._enviar_json(
                {
                    "status": "processado_evolution",
                    "evento_recebido": evento,
                    "resultado_lili": res,
                    "disparo_whatsapp": envio_wa,
                }
            )
            return

        if rota == "/webhook/whatsapp":
            evento = whatsapp_api.extrair_evento_webhook(body)
            if not evento:
                self._enviar_json({"status": "ignorado_sem_mensagem"})
                return
            if evento.get("nome_perfil_whatsapp"):
                lead_ex = motor_lili.crm.obter_ou_criar_lead(evento["telefone"])
                if not lead_ex.nome:
                    motor_lili.crm.atualizar_lead(evento["telefone"], nome=evento["nome_perfil_whatsapp"])
            res = motor_lili.processar_mensagem(
                telefone=evento["telefone"],
                mensagem=evento["texto"],
                origem=evento["origem"],
                campanha=evento["campanha"],
            )
            envio_wa = None
            if res.get("resposta_lili"):
                envio_wa = whatsapp_api.enviar_mensagem_texto(evento["telefone"], res["resposta_lili"])
            self._enviar_json(
                {
                    "status": "processado",
                    "evento_recebido": evento,
                    "resultado_lili": res,
                    "disparo_whatsapp": envio_wa,
                }
            )
            return

        if rota == "/webhook/lead-site":
            tel = body.get("telefone", "5548999990002")
            nome = body.get("nome")
            empreendimento = body.get("empreendimento_interesse")
            motor_lili.crm.obter_ou_criar_lead(tel, origem=body.get("origem", "Formulário do Site"), campanha=body.get("campanha"))
            motor_lili.crm.atualizar_lead(tel, nome=nome, email=body.get("email"), imovel_maior_interesse=empreendimento)
            saudacao = f", {nome}" if nome else ""
            trecho = f"Vi que você se interessou pelo {empreendimento}. " if empreendimento else ""
            msg = (
                f"Oi{saudacao}! Aqui é a Lili, assistente virtual da Construtora Demo 😊\n"
                f"{trecho}Me conta: você tá procurando seu primeiro imóvel pra morar ou pra investir?"
            )
            motor_lili.crm.registrar_mensagem_historico(tel, "lili", msg)
            disparo = whatsapp_api.enviar_mensagem_texto(tel, msg)
            self._enviar_json({"status": "lead_registrado_e_contatado", "primeira_mensagem_lili": msg, "disparo_whatsapp": disparo})
            return

        m_follow = re.fullmatch(r"/api/leads/([^/]+)/followup/([^/]+)", rota)
        if m_follow:
            tel, etapa_id = m_follow.group(1), m_follow.group(2)
            self._enviar_json(motor_followup.disparar_followup(tel, etapa_id))
            return

        m_conf = re.fullmatch(r"/api/leads/([^/]+)/confirmar-visita", rota)
        if m_conf:
            tel = m_conf.group(1)
            res = motor_followup.confirmar_visita_pelo_vendedor(
                telefone=tel,
                horario_confirmado=body.get("horario_confirmado", "15h00"),
                local=body.get("local", "Stand Central - Tubarão"),
                vendedor=body.get("vendedor"),
            )
            self._enviar_json(res)
            return

        m_lemb = re.fullmatch(r"/api/leads/([^/]+)/lembrete-visita", rota)
        if m_lemb:
            tel = m_lemb.group(1)
            self._enviar_json(motor_followup.disparar_lembrete_visita_dia_anterior(tel))
            return

        m_sla = re.fullmatch(r"/api/leads/([^/]+)/verificar-sla", rota)
        if m_sla:
            tel = m_sla.group(1)
            res = motor_followup.verificar_sla_vendedor_e_redistribuir(
                telefone=tel,
                minutos_decorridos_simulacao=body.get("minutos_decorridos_simulacao", 35),
            )
            self._enviar_json(res)
            return

        m_assumir = re.fullmatch(r"/api/leads/([^/]+)/vendedor-assumir", rota)
        if m_assumir:
            self._enviar_json(motor_lili.crm.definir_controle_vendedor(m_assumir.group(1), assumir=True))
            return

        m_devolver = re.fullmatch(r"/api/leads/([^/]+)/vendedor-devolver", rota)
        if m_devolver:
            self._enviar_json(motor_lili.crm.definir_controle_vendedor(m_devolver.group(1), assumir=False))
            return

        m_reset = re.fullmatch(r"/api/leads/([^/]+)/resetar", rota)
        if m_reset:
            tel_limpo = "".join(c for c in m_reset.group(1) if c.isdigit() or c == "+") or "padrao"
            if tel_limpo in motor_lili.crm._leads:
                del motor_lili.crm._leads[tel_limpo]
                motor_lili.crm._salvar()
            novo = motor_lili.crm.obter_ou_criar_lead(tel_limpo)
            self._enviar_json({"status": "resetado", "lead": novo.__dict__})
            return

        if rota == "/api/mcmv/enquadrar":
            res = calcular_pre_enquadramento(
                renda_bruta=body.get("renda_bruta"),
                faixa_informada=body.get("faixa_informada"),
                cidade=body.get("cidade", "Tubarão"),
                valor_imovel=body.get("valor_imovel"),
                imovel_novo=body.get("imovel_novo", True),
            )
            self._enviar_json(res)
            return

        if rota == "/api/kb/institucional":
            res = motor_lili.institucional.salvar(body.get("dados", {}))
            self._enviar_json(res)
            return

        if rota == "/api/kb/xml":
            xml_content = (body.get("xml_content") or "").strip()
            sucesso = motor_lili.catalogo.recarregar_base(forcar=True, xml_content_override=xml_content)
            if sucesso:
                settings.XML_IMOVEIS_PATH.write_text(xml_content, encoding="utf-8")
            self._enviar_json(
                {
                    "sucesso": sucesso,
                    "total_imoveis": len(motor_lili.catalogo.listar_disponiveis()),
                }
            )
            return

        if rota == "/api/kb/prompt":
            novo_prompt = (body.get("system_prompt") or "").strip()
            if novo_prompt:
                (BASE_DIR / "GEMINI.md").write_text(novo_prompt, encoding="utf-8")
                motor_lili.system_prompt = novo_prompt
            self._enviar_json({"status": "salvo"})
            return

        if rota == "/api/imoveis/admin/salvar":
            self._enviar_json(motor_lili.catalogo.salvar_ou_atualizar_imovel(body))
            return

        if rota == "/api/imoveis/admin/excluir":
            self._enviar_json(motor_lili.catalogo.remover_imovel(body.get("codigo", "")))
            return

        self._enviar_json({"erro": "Rota POST não encontrada"}, status=404)


def iniciar_servidor(host: str = "127.0.0.1", port: int = 8000) -> None:
    servidor = ThreadingHTTPServer((host, port), LiliHTTPHandler)
    print(f"[Lili IA] Console Web ativo em: http://127.0.0.1:{port}/", flush=True)
    print(f"[Lili IA] Dica: se o navegador nao atualizar, acesse via janela anonima ou Ctrl + Shift + R", flush=True)
    servidor.serve_forever()


if __name__ == "__main__":
    iniciar_servidor()
