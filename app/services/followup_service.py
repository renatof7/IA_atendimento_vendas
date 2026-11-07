"""
Motor de Follow-up, Nutrição, Lembrete de Visita e Monitoramento de SLA (Seções 8, 10 e 12).
Regras estritas:
1. Follow-up sem valor é ruído: a Lili nunca envia apenas 'E aí?' ou 'Conseguiu ver?'.
2. Cadência oficial: 2h, 24h, Dia 3, Dia 7, Dia 15 e Dia 30.
3. Após 24 horas sem resposta do cliente, só envia mensagens com modelos aprovados pela Meta (WhatsApp Business API).
4. Se o cliente pedir para parar (Opt-Out LGPD) ou o vendedor assumir, para imediatamente.
5. Sem resposta após o Dia 30, o lead fica como 'sem retorno' e segue na nutrição de campanhas.
6. Lembrete de visita no dia anterior: só é enviado DEPOIS que o vendedor confirmar a visita.
7. Monitor de SLA: se o prazo do vendedor estourar (Quente: 30min, Morno: 4h, Frio: 48h),
   o lead é redistribuído automaticamente e o gestor é avisado.
"""

from datetime import datetime, timedelta
from typing import Optional

from app.services.crm_service import ServicoCRMAgendor, RegistroLeadCRM
from app.services.xml_catalog import CatalogoImoveisXML
from app.agent.guardrails import aplicar_guardrails_resposta


EQUIPE_VENDEDORES_PLANTAO = [
    "Carlos Eduardo",
    "Fernanda Lima",
    "Roberto Alves",
    "Juliana Costa",
]

# Ordem cronológica das etapas da cadência (Seção 10)
CADENCIA_ETAPAS = [
    {"id": "2h", "horas_minimas": 2, "usa_template_meta": False, "template_meta": None},
    {"id": "24h", "horas_minimas": 24, "usa_template_meta": False, "template_meta": None},
    {"id": "D3", "horas_minimas": 72, "usa_template_meta": True, "template_meta": "meta_imob_novidade_d3"},
    {"id": "D7", "horas_minimas": 168, "usa_template_meta": True, "template_meta": "meta_imob_prova_social_d7"},
    {"id": "D15", "horas_minimas": 360, "usa_template_meta": True, "template_meta": "meta_imob_andamento_obra_d15"},
    {"id": "D30", "horas_minimas": 720, "usa_template_meta": True, "template_meta": "meta_imob_campanha_d30"},
]


class MotorFollowUpENutricao:
    """Gerencia a régua de follow-up (2h a D30), lembretes de visita e SLA de transbordo."""

    def __init__(
        self,
        crm: ServicoCRMAgendor,
        catalogo: Optional[CatalogoImoveisXML] = None,
    ):
        self.crm = crm
        self.catalogo = catalogo or CatalogoImoveisXML()
        self.alertas_gestor: list[dict] = []

    def pode_enviar_followup(self, lead: RegistroLeadCRM) -> tuple[bool, str]:
        """Verifica todas as travas de segurança e LGPD antes de qualquer disparo."""
        if lead.opt_out_lgpd:
            return False, "Bloqueado: cliente solicitou opt-out (LGPD)."
        if lead.vendedor_assumiu:
            return False, f"Bloqueado: vendedor {lead.vendedor_responsavel} já assumiu o atendimento."
        if lead.etapa in ("sem perfil", "sem retorno", "opt-out (LGPD)"):
            return False, f"Bloqueado: lead está na etapa '{lead.etapa}'."
        return True, "OK"

    def gerar_mensagem_etapa(self, lead: RegistroLeadCRM, etapa_id: str) -> dict:
        """
        Gera a mensagem de valor correspondente à etapa da cadência (2h, 24h, D3, D7, D15, D30),
        contextualizada com o nome do cliente, cidade e imóvel de interesse.
        """
        nome = lead.nome or "tudo bem"
        saudacao_nome = f"Oi, {lead.nome}!" if lead.nome else "Oi! Tudo bem?"
        imovel_ref = lead.imovel_maior_interesse or "nosso empreendimento"
        cidade_ref = lead.cidade if lead.cidade and "Qualquer" not in lead.cidade else "sua região"

        # Busca detalhes do imóvel no XML se houver código apresentado
        diferencial_imovel = "condições especiais pelo Minha Casa, Minha Vida"
        if lead.imoveis_apresentados:
            det = self.catalogo.detalhar_imovel(lead.imoveis_apresentados[0])
            if det:
                imovel_ref = det["nome"]
                diferencial_imovel = det["diferencial"].lower()

        if etapa_id == "2h":
            # 2 horas sem resposta: retomar o ponto da conversa com uma pergunta simples
            if not lead.cidade:
                texto = (
                    f"{saudacao_nome} Sei que a correria do dia a dia é grande 😊\n"
                    "Pra eu separar as melhores opções pra você: em qual cidade você prefere morar?"
                )
            elif not lead.renda_bruta_familiar_faixa:
                texto = (
                    f"{saudacao_nome} Pra eu ver em qual faixa do Minha Casa, Minha Vida você se encaixa:\n"
                    "Qual é a faixa de renda bruta mensal aí da família, mais ou menos?"
                )
            else:
                texto = (
                    f"{saudacao_nome} Ficou alguma dúvida sobre o {imovel_ref} 😊\n"
                    "Se quiser, já vemos qual dia fica melhor pra você conhecer de perto!"
                )
            usa_template = False
            template_nome = None

        elif etapa_id == "24h":
            # 24 horas: uma informação útil sobre o imóvel de interesse ou sobre o programa
            texto = (
                f"{saudacao_nome} Passando pra compartilhar uma informação útil pra quem quer sair do aluguel 😊\n"
                f"No {imovel_ref}, além de contar com {diferencial_imovel}, você pode usar seu FGTS e avaliar o subsídio da Caixa.\n"
                "Quer que a gente veja como ficaria no seu perfil?"
            )
            usa_template = False
            template_nome = None

        elif etapa_id == "D3":
            # Dia 3: uma novidade aprovada (nova unidade, condição ou foto do decorado)
            texto = (
                f"{saudacao_nome} Lembrei de você porque temos novidade bacana no {imovel_ref} pra quem busca o primeiro imóvel 😊\n"
                "As visitas ao plantão estão abertas essa semana.\n"
                "Posso te contar como funciona em 2 minutinhos?"
            )
            usa_template = True
            template_nome = "meta_imob_novidade_d3"

        elif etapa_id == "D7":
            # Dia 7: prova social (família recebendo as chaves ou depoimento real)
            texto = (
                f"{saudacao_nome} Essa semana mais famílias realizaram o sonho de pegar as chaves e sair do aluguel 😊\n"
                "Muita gente começa com uma simulação rápida e descobre que a parcela cabe no bolso.\n"
                "Que tal a gente dar esse primeiro passo sem compromisso?"
            )
            usa_template = True
            template_nome = "meta_imob_prova_social_d7"

        elif etapa_id == "D15":
            # Dia 15: andamento da obra (foto atualizada da construção)
            texto = (
                f"{saudacao_nome} O ritmo das obras em {cidade_ref} segue avançando super bem 😊\n"
                f"Se você ainda planeja se mudar pro {imovel_ref}, vale muito a pena acompanhar de perto antes que a tabela mude.\n"
                "Quer receber as fotos atualizadas ou agendar uma visita rápida?"
            )
            usa_template = True
            template_nome = "meta_imob_andamento_obra_d15"

        elif etapa_id == "D30":
            # Dia 30: nova condição comercial ou campanha vigente
            texto = (
                f"{saudacao_nome} Entramos em uma nova campanha comercial para imóveis do Minha Casa, Minha Vida 😊\n"
                "Se o seu plano de comprar seu imóvel continua de pé, posso pedir pro nosso especialista atualizar sua simulação?\n"
                "Seu lar, sua história."
            )
            usa_template = True
            template_nome = "meta_imob_campanha_d30"

        else:
            raise ValueError(f"Etapa de follow-up inválida: {etapa_id}")

        texto_validado = aplicar_guardrails_resposta(texto)
        return {
            "etapa_followup": etapa_id,
            "usa_template_meta": usa_template,
            "template_meta": template_nome,
            "mensagem": texto_validado,
        }

    def disparar_followup(
        self,
        telefone: str,
        etapa_id: str,
    ) -> dict:
        """
        Executa o disparo de uma etapa específica da cadência ('2h', '24h', 'D3', 'D7', 'D15', 'D30' ou 'pos_d30').
        Se for 'pos_d30' (após 30 dias sem resposta), marca como 'sem retorno' no Agendor.
        """
        lead = self.crm.obter_ou_criar_lead(telefone)
        permitido, motivo = self.pode_enviar_followup(lead)
        if not permitido:
            return {"enviado": False, "motivo": motivo, "etapa_atual_lead": lead.etapa}

        if etapa_id == "pos_d30":
            lead.etapa = "sem retorno"
            self.crm._salvar()
            return {
                "enviado": False,
                "status": "marcado_sem_retorno",
                "motivo": "Sem resposta após o Dia 30: lead marcado como 'sem retorno' e encaminhado à nutrição de campanhas.",
                "etapa_atual_lead": lead.etapa,
            }

        dados_msg = self.gerar_mensagem_etapa(lead, etapa_id)
        if etapa_id not in lead.etapas_followup_enviadas:
            lead.etapas_followup_enviadas.append(etapa_id)
        self.crm.registrar_mensagem_historico(telefone, "lili", dados_msg["mensagem"])

        return {
            "enviado": True,
            "etapa_followup": etapa_id,
            "usa_template_meta": dados_msg["usa_template_meta"],
            "template_meta": dados_msg["template_meta"],
            "mensagem_enviada": dados_msg["mensagem"],
            "etapas_ja_enviadas": list(lead.etapas_followup_enviadas),
        }

    def verificar_proximo_followup_devido(
        self,
        telefone: str,
        horas_sem_resposta: float,
    ) -> dict:
        """
        Avalia quantas horas se passaram desde a última resposta do cliente e dispara
        automaticamente a etapa correspondente da régua (2h -> 24h -> D3 -> D7 -> D15 -> D30 -> sem retorno).
        """
        lead = self.crm.obter_ou_criar_lead(telefone)
        permitido, motivo = self.pode_enviar_followup(lead)
        if not permitido:
            return {"acao": "nenhuma", "motivo": motivo}

        # Se passou de 30 dias (720h) e o D30 já foi enviado, encerra como "sem retorno"
        if horas_sem_resposta > 744 and "D30" in lead.etapas_followup_enviadas:
            return self.disparar_followup(telefone, "pos_d30")

        # Procura a etapa aplicável ainda não enviada
        etapa_alvo: Optional[str] = None
        for item in CADENCIA_ETAPAS:
            if horas_sem_resposta >= item["horas_minimas"] and item["id"] not in lead.etapas_followup_enviadas:
                etapa_alvo = item["id"]

        if etapa_alvo:
            return self.disparar_followup(telefone, etapa_alvo)

        return {
            "acao": "aguardando_janela",
            "horas_sem_resposta": horas_sem_resposta,
            "etapas_ja_enviadas": list(lead.etapas_followup_enviadas),
        }

    def confirmar_visita_pelo_vendedor(
        self,
        telefone: str,
        horario_confirmado: str,
        local: str = "Stand / Plantão Central",
        vendedor: Optional[str] = None,
    ) -> dict:
        """
        Ação exclusiva do vendedor no CRM: confirma o horário da visita que estava 'a confirmar'.
        Habilita o envio do lembrete automático no dia anterior (Seção 8).
        """
        lead = self.crm.obter_ou_criar_lead(telefone)
        if vendedor:
            lead.vendedor_responsavel = vendedor
        lead.status_visita = "confirmada"
        lead.horario_visita_confirmado = horario_confirmado
        lead.local_visita = local
        self.crm._salvar()
        return {
            "status": "visita_confirmada_pelo_vendedor",
            "telefone": lead.telefone,
            "horario_visita_confirmado": lead.horario_visita_confirmado,
            "local_visita": lead.local_visita,
            "vendedor_responsavel": lead.vendedor_responsavel,
        }

    def disparar_lembrete_visita_dia_anterior(self, telefone: str) -> dict:
        """
        Envia o lembrete no dia anterior à visita (Seção 8).
        REGRA DE OURO: Só envia depois que o vendedor confirmar a visita ('status_visita == confirmada').
        """
        lead = self.crm.obter_ou_criar_lead(telefone)
        if lead.opt_out_lgpd:
            return {"enviado": False, "motivo": "Cliente em opt-out LGPD."}

        if lead.status_visita != "confirmada" or not lead.horario_visita_confirmado:
            return {
                "enviado": False,
                "motivo": (
                    "Visitas com status 'a confirmar' não disparam lembrete. "
                    "O vendedor precisa confirmar o horário primeiro (Seção 8)."
                ),
            }

        nome = lead.nome or "tudo bem"
        hora = lead.horario_visita_confirmado
        local = lead.local_visita or "nosso plantão central"
        vendedor = lead.vendedor_responsavel

        mensagem_lembrete = aplicar_guardrails_resposta(
            f"Oi, {nome}! Passando pra lembrar da sua visita amanhã, às {hora}, no {local} 😊\n"
            f"O {vendedor} já tá com tudo preparado pra sua simulação. Até amanhã!"
        )
        lead.lembrete_visita_enviado = True
        self.crm.registrar_mensagem_historico(telefone, "lili", mensagem_lembrete)

        return {
            "enviado": True,
            "tipo": "lembrete_visita_dia_anterior",
            "mensagem_enviada": mensagem_lembrete,
        }

    def verificar_sla_vendedor_e_redistribuir(
        self,
        telefone: str,
        minutos_decorridos_simulacao: Optional[int] = None,
    ) -> dict:
        """
        Monitora o prazo para o vendedor assumir o lead (Seção 12):
        - Quente: até 30 minutos no horário comercial
        - Morno: até 4 horas (240 minutos) no horário comercial
        - Frio: até 48 horas (2880 minutos)
        Se o prazo estourar e o vendedor ainda não tiver assumido, redistribui o lead
        para outro vendedor de plantão e avisa o gestor!
        """
        lead = self.crm.obter_ou_criar_lead(telefone)

        if lead.vendedor_assumiu:
            return {
                "sla_estourado": False,
                "status": "atendimento_ja_assumido",
                "vendedor_atual": lead.vendedor_responsavel,
            }

        # Limite em minutos conforme temperatura (Seção 12)
        if lead.temperatura == "Quente":
            limite_minutos = 30
        elif lead.temperatura == "Morno":
            limite_minutos = 240
        else:
            limite_minutos = 2880

        if minutos_decorridos_simulacao is not None:
            minutos_passados = minutos_decorridos_simulacao
        elif lead.data_hora_transferencia:
            dt_trans = datetime.fromisoformat(lead.data_hora_transferencia)
            minutos_passados = int((datetime.now() - dt_trans).total_seconds() // 60)
        else:
            minutos_passados = 0

        if minutos_passados <= limite_minutos:
            return {
                "sla_estourado": False,
                "minutos_decorridos": minutos_passados,
                "limite_minutos_sla": limite_minutos,
                "vendedor_atual": lead.vendedor_responsavel,
            }

        # Prazo estourou! Redistribui o lead e avisa o gestor (Seção 12)
        vendedor_anterior = lead.vendedor_responsavel
        idx_atual = (
            EQUIPE_VENDEDORES_PLANTAO.index(vendedor_anterior)
            if vendedor_anterior in EQUIPE_VENDEDORES_PLANTAO
            else 0
        )
        novo_vendedor = EQUIPE_VENDEDORES_PLANTAO[(idx_atual + 1) % len(EQUIPE_VENDEDORES_PLANTAO)]

        lead.vendedor_responsavel = novo_vendedor
        lead.sla_estourado = True
        lead.data_hora_transferencia = datetime.now().isoformat()
        registro_redist = (
            f"SLA de {limite_minutos} min estourado ({minutos_passados} min sem assumir). "
            f"Redistribuído de {vendedor_anterior} para {novo_vendedor}."
        )
        lead.historico_redistribuicao.append(registro_redist)
        self.crm._salvar()

        alerta = {
            "timestamp": datetime.now().isoformat(),
            "telefone_lead": lead.telefone,
            "nome_lead": lead.nome or "Cliente",
            "temperatura": lead.temperatura,
            "vendedor_anterior": vendedor_anterior,
            "novo_vendedor": novo_vendedor,
            "mensagem_gestor": (
                f"🚨 [ALERTA GESTOR] Lead {lead.temperatura.upper()} ({lead.nome or lead.telefone}) "
                f"ultrapassou o SLA de {limite_minutos} min com {vendedor_anterior}. "
                f"Redistribuído automaticamente para {novo_vendedor}."
            ),
        }
        self.alertas_gestor.append(alerta)

        return {
            "sla_estourado": True,
            "vendedor_anterior": vendedor_anterior,
            "novo_vendedor": novo_vendedor,
            "minutos_decorridos": minutos_passados,
            "limite_minutos_sla": limite_minutos,
            "alerta_gestor": alerta["mensagem_gestor"],
        }
