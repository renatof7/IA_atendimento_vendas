"""
API FastAPI e Painel Web de Simulação em Tempo Real — Lili IA (Motor de Pré-Vendas Imobiliárias).
Inclui:
- Atendimento WhatsApp com Anthropic Claude Tool Use / Motor Local
- Ficha em tempo real no CRM Agendor + Resumo de 6 Linhas
- Motor de Follow-up e Nutrição (2h, 24h, D3, D7, D15, D30, Sem Retorno)
- Confirmação de Visita pelo Vendedor + Lembrete no Dia Anterior
- Monitor de SLA do Vendedor + Redistribuição Automática e Alerta ao Gestor
"""

from typing import Optional
from fastapi import FastAPI, Query, Response
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.domain.mcmv import calcular_pre_enquadramento
from app.agent.engine import MotorLili
from app.services.followup_service import MotorFollowUpENutricao
from app.services.whatsapp_connector import WhatsAppCloudConnector
from app.services.evolution_connector import EvolutionAPIConnector
from app.web_ui import WEB_CONSOLE_HTML

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Motor de Pré-Vendas MCMV 2026 da Lili "
        "integrado com GroqCloud (Llama 3.3 70B), Evolution API (QR Code), Base XML, Agendor CRM e Motor de Follow-up/SLA."
    ),
)

motor_lili = MotorLili()
motor_followup = MotorFollowUpENutricao(crm=motor_lili.crm, catalogo=motor_lili.catalogo)
whatsapp_api = WhatsAppCloudConnector()
evolution_api = EvolutionAPIConnector()


class MensagemWhatsAppRequest(BaseModel):
    telefone: str = Field(default="5548999990001", description="Telefone WhatsApp do lead")
    mensagem: str = Field(..., description="Texto enviado pelo lead")
    origem: Optional[str] = Field(default="Instagram Ads", description="Canal de origem do lead")
    campanha: Optional[str] = Field(default="MCMV_2026_SairDoAluguel", description="Campanha/UTM")


class PreEnquadramentoRequest(BaseModel):
    renda_bruta: Optional[float] = None
    faixa_informada: Optional[str] = None
    cidade: Optional[str] = "Tubarão"
    valor_imovel: Optional[float] = None
    imovel_novo: bool = True


class ConfirmarVisitaRequest(BaseModel):
    horario_confirmado: str = Field(default="15h00", description="Horário confirmado pelo vendedor")
    local: str = Field(default="Stand Central - Tubarão", description="Local confirmado")
    vendedor: Optional[str] = None


class VerificarSLARequest(BaseModel):
    minutos_decorridos_simulacao: Optional[int] = Field(
        default=35,
        description="Minutos simulados desde a transferência para testar estouro de SLA",
    )


class LeadExternoSitePortalRequest(BaseModel):
    telefone: str = Field(..., description="Telefone WhatsApp do lead")
    nome: Optional[str] = Field(default=None, description="Nome preenchido no formulário/portal")
    email: Optional[str] = Field(default=None)
    origem: str = Field(default="Formulário do Site", description="Site, Landing Page ou Portal Imobiliário")
    campanha: Optional[str] = Field(default=None, description="UTM ou nome da campanha")
    empreendimento_interesse: Optional[str] = Field(default=None, description="Empreendimento de origem")


@app.get("/webhook/whatsapp", response_class=PlainTextResponse)
def validar_webhook_whatsapp_meta(
    hub_mode: Optional[str] = Query(default=None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(default=None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(default=None, alias="hub.challenge"),
):
    """Handshake oficial de verificação de Webhook da WhatsApp Business Cloud API (Meta)."""
    ok, resposta = whatsapp_api.validar_webhook_meta(hub_mode, hub_verify_token, hub_challenge)
    if not ok:
        return PlainTextResponse(content=resposta, status_code=403)
    return PlainTextResponse(content=resposta, status_code=200)


@app.post("/webhook/whatsapp")
def receber_webhook_whatsapp_meta(payload: dict) -> dict:
    """
    Recebe eventos da WhatsApp Business Cloud API (Meta), identifica origem (Ads/Placa/Site/Direto),
    processa no Motor da Lili, grava no Agendor CRM e dispara a resposta no WhatsApp.
    """
    evento = whatsapp_api.extrair_evento_webhook(payload)
    if not evento:
        return {"status": "ignorado_sem_mensagem"}

    if evento.get("nome_perfil_whatsapp"):
        lead_existente = motor_lili.crm.obter_ou_criar_lead(evento["telefone"])
        if not lead_existente.nome:
            motor_lili.crm.atualizar_lead(evento["telefone"], nome=evento["nome_perfil_whatsapp"])

    resultado = motor_lili.processar_mensagem(
        telefone=evento["telefone"],
        mensagem=evento["texto"],
        origem=evento["origem"],
        campanha=evento["campanha"],
    )

    envio_wa = None
    if resultado.get("resposta_lili"):
        envio_wa = whatsapp_api.enviar_mensagem_texto(
            telefone=evento["telefone"],
            texto=resultado["resposta_lili"],
        )

    return {
        "status": "processado",
        "evento_recebido": evento,
        "resultado_lili": resultado,
        "disparo_whatsapp": envio_wa,
    }


@app.post("/webhook/evolution")
def receber_webhook_evolution(payload: dict) -> dict:
    """
    Recebe mensagens do WhatsApp via Evolution API (QR Code):
    1. Extrai texto, remetente e metadados
    2. Simula status 'digitando...'
    3. Processa no Motor da Lili (GroqCloud Llama 3.3 70B)
    4. Envia resposta de volta pelo WhatsApp via Evolution API.
    """
    evento = evolution_api.extrair_evento_webhook(payload)
    if not evento:
        return {"status": "ignorado_sem_mensagem"}

    if evento.get("nome_perfil_whatsapp"):
        lead_existente = motor_lili.crm.obter_ou_criar_lead(evento["telefone"])
        if not lead_existente.nome:
            motor_lili.crm.atualizar_lead(evento["telefone"], nome=evento["nome_perfil_whatsapp"])

    # Presença digitando no WhatsApp
    evolution_api.enviar_presenca_digitando(evento["telefone"], delay_ms=1200)

    resultado = motor_lili.processar_mensagem(
        telefone=evento["telefone"],
        mensagem=evento["texto"],
        origem=evento["origem"],
        campanha=evento["campanha"],
    )

    envio_wa = None
    if resultado.get("resposta_lili"):
        envio_wa = evolution_api.enviar_mensagem_texto(
            telefone=evento["telefone"],
            texto=resultado["resposta_lili"],
        )

    return {
        "status": "processado_evolution",
        "evento_recebido": evento,
        "resultado_lili": resultado,
        "disparo_whatsapp": envio_wa,
    }


@app.get("/api/evolution/status")
def status_conexao_evolution() -> dict:
    """Verifica o estado da instância do WhatsApp na Evolution API."""
    return evolution_api.verificar_estado_conexao()


@app.get("/api/evolution/qrcode")
def qrcode_conexao_evolution() -> dict:
    """Retorna o QR Code (Base64) gerado pela Evolution API para parear no celular."""
    return evolution_api.obter_qrcode()


@app.post("/webhook/lead-site")
def receber_lead_formulario_ou_portal(payload: LeadExternoSitePortalRequest) -> dict:
    """
    Recebe leads de Formulários do Site, Landing Pages e Portais Imobiliários:
    1. Cria ou atualiza no CRM Agendor (sem duplicar telefone)
    2. Dispara imediatamente o primeiro contato da Lili no WhatsApp citando o empreendimento de origem.
    """
    motor_lili.crm.obter_ou_criar_lead(
        telefone=payload.telefone,
        origem=payload.origem,
        campanha=payload.campanha,
    )
    motor_lili.crm.atualizar_lead(
        payload.telefone,
        nome=payload.nome,
        email=payload.email,
        imovel_maior_interesse=payload.empreendimento_interesse,
    )

    saudacao_nome = f", {payload.nome}" if payload.nome else ""
    trecho_imovel = (
        f"Vi que você se interessou pelo {payload.empreendimento_interesse}. "
        if payload.empreendimento_interesse
        else ""
    )
    primeira_msg = (
        f"Oi{saudacao_nome}! Aqui é a Lili, assistente virtual da Construtora Demo 😊\n"
        f"{trecho_imovel}Me conta: você tá procurando seu primeiro imóvel pra morar ou pra investir?"
    )
    motor_lili.crm.registrar_mensagem_historico(payload.telefone, "lili", primeira_msg)
    disparo = whatsapp_api.enviar_mensagem_texto(payload.telefone, primeira_msg)

    return {
        "status": "lead_registrado_e_contatado",
        "primeira_mensagem_lili": primeira_msg,
        "disparo_whatsapp": disparo,
    }


@app.get("/api/integracoes/logs")
def consultar_logs_integracoes() -> dict:
    """Retorna os últimos logs enviados à Evolution API, WhatsApp Cloud e Agendor CRM API v3."""
    return {
        "evolution_api_outbox": evolution_api.outbox_logs[-10:],
        "whatsapp_cloud_api_outbox": whatsapp_api.outbox_logs[-10:],
        "agendor_crm_v3_sync": motor_lili.crm.agendor_api.sync_logs[-10:],
    }


@app.get("/api/kb")
def obter_bases_conhecimento() -> dict:
    """Retorna a Base Institucional (JSON), a Base de Imóveis (XML) e o System Prompt (GEMINI.md)."""
    xml_txt = (
        settings.XML_IMOVEIS_PATH.read_text(encoding="utf-8")
        if settings.XML_IMOVEIS_PATH.exists()
        else ""
    )
    return {
        "institucional": motor_lili.institucional.dados,
        "xml_imoveis": xml_txt,
        "system_prompt": motor_lili.system_prompt,
    }


@app.post("/api/kb/institucional")
def salvar_base_institucional_endpoint(payload: dict) -> dict:
    """Salva e recarrega a base institucional da construtora."""
    novos_dados = payload.get("dados", {})
    return motor_lili.institucional.salvar(novos_dados)


@app.post("/api/kb/xml")
def salvar_base_xml_endpoint(payload: dict) -> dict:
    """Valida o XML enviado; se válido, grava em data/imoveis.xml e atualiza o catálogo."""
    xml_content = (payload.get("xml_content") or "").strip()
    sucesso = motor_lili.catalogo.recarregar_base(forcar=True, xml_content_override=xml_content)
    if sucesso:
        settings.XML_IMOVEIS_PATH.write_text(xml_content, encoding="utf-8")
    return {
        "sucesso": sucesso,
        "total_imoveis": len(motor_lili.catalogo.listar_disponiveis()),
    }


@app.post("/api/kb/prompt")
def salvar_system_prompt_endpoint(payload: dict) -> dict:
    """Salva o System Prompt em GEMINI.md e atualiza o motor da Lili em tempo real."""
    from app.config import BASE_DIR

    novo_prompt = (payload.get("system_prompt") or "").strip()
    if novo_prompt:
        (BASE_DIR / "GEMINI.md").write_text(novo_prompt, encoding="utf-8")
        motor_lili.system_prompt = novo_prompt
    return {"status": "salvo"}


@app.post("/api/chat")
def processar_mensagem_whatsapp(payload: MensagemWhatsAppRequest) -> dict:
    """Recebe uma mensagem do WhatsApp e retorna a resposta da Lili + estado do CRM."""
    res = motor_lili.processar_mensagem(
        telefone=payload.telefone,
        mensagem=payload.mensagem,
        origem=payload.origem,
        campanha=payload.campanha,
    )
    if res.get("resposta_lili"):
        if settings.WHATSAPP_PROVIDER == "evolution":
            evolution_api.enviar_mensagem_texto(payload.telefone, res["resposta_lili"])
        else:
            whatsapp_api.enviar_mensagem_texto(payload.telefone, res["resposta_lili"])
    return res


@app.get("/api/leads")
def listar_todos_leads_crm() -> dict:
    """Lista todos os leads do CRM para o painel de gestão de atendimentos e relatórios."""
    return {"leads": motor_lili.crm.listar_todos_leads()}


@app.get("/api/leads/{telefone}")
def consultar_lead_crm(telefone: str) -> dict:
    """Consulta o registro completo do lead no CRM Agendor + alertas do gestor."""
    lead = motor_lili.crm.obter_ou_criar_lead(telefone)
    resumo_6_linhas = motor_lili.crm.gerar_resumo_6_linhas(lead)
    return {
        "lead": lead.__dict__,
        "resumo_6_linhas_preview": resumo_6_linhas,
        "alertas_gestor": motor_followup.alertas_gestor[-5:],
    }


@app.post("/api/leads/{telefone}/followup/{etapa_id}")
def acionar_etapa_followup(telefone: str, etapa_id: str) -> dict:
    """
    Dispara uma etapa da cadência de Follow-up ('2h', '24h', 'D3', 'D7', 'D15', 'D30' ou 'pos_d30').
    """
    return motor_followup.disparar_followup(telefone=telefone, etapa_id=etapa_id)


@app.post("/api/leads/{telefone}/confirmar-visita")
def confirmar_visita_vendedor_endpoint(telefone: str, payload: ConfirmarVisitaRequest) -> dict:
    """Ação do vendedor para confirmar o horário da visita (habilita lembrete na véspera)."""
    return motor_followup.confirmar_visita_pelo_vendedor(
        telefone=telefone,
        horario_confirmado=payload.horario_confirmado,
        local=payload.local,
        vendedor=payload.vendedor,
    )


@app.post("/api/leads/{telefone}/lembrete-visita")
def disparar_lembrete_visita_endpoint(telefone: str) -> dict:
    """Dispara o lembrete do dia anterior à visita (apenas se o vendedor já confirmou)."""
    return motor_followup.disparar_lembrete_visita_dia_anterior(telefone=telefone)


@app.post("/api/leads/{telefone}/verificar-sla")
def verificar_sla_vendedor_endpoint(telefone: str, payload: VerificarSLARequest) -> dict:
    """Verifica se o SLA do vendedor estourou e redistribui automaticamente o lead."""
    return motor_followup.verificar_sla_vendedor_e_redistribuir(
        telefone=telefone,
        minutos_decorridos_simulacao=payload.minutos_decorridos_simulacao,
    )


@app.post("/api/leads/{telefone}/vendedor-assumir")
def vendedor_assumir_atendimento(telefone: str) -> dict:
    """Aciona o botão que desliga a IA naquele contato quando o vendedor assume."""
    return motor_lili.crm.definir_controle_vendedor(telefone, assumir=True)


@app.post("/api/leads/{telefone}/vendedor-devolver")
def vendedor_devolver_atendimento(telefone: str) -> dict:
    """Religa a IA naquele contato caso o vendedor devolva para a Lili."""
    return motor_lili.crm.definir_controle_vendedor(telefone, assumir=False)


@app.post("/api/leads/{telefone}/resetar")
def resetar_lead_teste(telefone: str) -> dict:
    """Limpa o histórico de um telefone específico para reiniciar testes de simulação."""
    tel_limpo = "".join(c for c in telefone if c.isdigit() or c == "+") or "padrao"
    if tel_limpo in motor_lili.crm._leads:
        del motor_lili.crm._leads[tel_limpo]
        motor_lili.crm._salvar()
    novo = motor_lili.crm.obter_ou_criar_lead(tel_limpo)
    return {"status": "resetado", "lead": novo.__dict__}


@app.get("/api/imoveis")
def buscar_imoveis_endpoint(
    cidade: Optional[str] = None,
    bairro: Optional[str] = None,
    tipo: Optional[str] = None,
    quartos: Optional[int] = None,
    valor_maximo: Optional[float] = None,
    faixa_mcmv: Optional[str] = None,
    renda_bruta: Optional[float] = None,
) -> dict:
    """Executa a ferramenta de busca na base XML vigente."""
    return motor_lili.catalogo.buscar_imoveis(
        cidade=cidade,
        bairro=bairro,
        tipo=tipo,
        quartos=quartos,
        valor_maximo=valor_maximo,
        faixa_mcmv=faixa_mcmv,
        renda_bruta=renda_bruta,
    )


@app.get("/api/imoveis/admin")
def listar_imoveis_admin_endpoint() -> dict:
    """Lista todos os imóveis em formato estruturado para os cards da tela de gestão."""
    return {"imoveis": motor_lili.catalogo.listar_todos_admin()}


@app.post("/api/imoveis/admin/salvar")
def salvar_imovel_admin_endpoint(payload: dict) -> dict:
    """Cadastra ou edita um imóvel pelo formulário amigável e atualiza o XML oficial."""
    return motor_lili.catalogo.salvar_ou_atualizar_imovel(payload)


@app.post("/api/imoveis/admin/excluir")
def excluir_imovel_admin_endpoint(payload: dict) -> dict:
    """Remove um imóvel pelo código e atualiza o XML oficial."""
    return motor_lili.catalogo.remover_imovel(payload.get("codigo", ""))


@app.post("/api/mcmv/enquadrar")
def enquadrar_mcmv_endpoint(payload: PreEnquadramentoRequest) -> dict:
    """Executa o cálculo interno da Tabela MCMV 2026."""
    return calcular_pre_enquadramento(
        renda_bruta=payload.renda_bruta,
        faixa_informada=payload.faixa_informada,
        cidade=payload.cidade,
        valor_imovel=payload.valor_imovel,
        imovel_novo=payload.imovel_novo,
    )


@app.get("/", response_class=HTMLResponse)
def simulador_web() -> Response:
    """Interface Web interativa para testar a Lili (WhatsApp + Agendor CRM + Follow-up/SLA + Editor KB)."""
    import importlib
    import app.web_ui
    importlib.reload(app.web_ui)
    return HTMLResponse(
        content=app.web_ui.WEB_CONSOLE_HTML,
        headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
    )

