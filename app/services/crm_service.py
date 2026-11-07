"""
Serviço de CRM (Agendor) e Gestão de Estado do Lead em Tempo Real.
Regras da Seção 12 e 14:
- Cada informação é gravada no Agendor assim que coletada, e não só no fim.
- Ao transferir, grava um resumo de até 6 linhas contendo: quem é o cliente,
  origem, o que busca, capacidade de compra, momento, imóvel de maior interesse,
  dúvidas/objeções em aberto e próximo passo sugerido.
- Suporta botão de desligamento manual ('vendedor_assumiu'): quando ativo, a Lili
  para de responder naquele contato e só volta se o vendedor devolver.
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.config import settings
from app.domain.mcmv import calcular_pre_enquadramento
from app.domain.scoring import calcular_pontuacao_e_temperatura


@dataclass
class RegistroLeadCRM:
    telefone: str
    nome: Optional[str] = None
    email: Optional[str] = None
    origem: str = "WhatsApp direto"
    campanha: Optional[str] = None
    anuncio_utm: Optional[str] = None
    data_hora_entrada: str = field(default_factory=lambda: datetime.now().isoformat())
    data_hora_primeira_resposta: Optional[str] = None

    # Qualificação (12 itens)
    objetivo: Optional[str] = None  # morar, investir, outro
    primeiro_imovel: Optional[str] = None  # sim, não
    cidade: Optional[str] = None
    tipo_imovel: Optional[str] = None
    quartos: Optional[int] = None
    renda_bruta_familiar_faixa: Optional[str] = None
    renda_bruta_valor_aproximado: Optional[float] = None
    tipo_renda: Optional[str] = None  # formal, informal, mista, PJ
    fgts_mais_3_anos: Optional[str] = None  # sim, não, prefiro não informar
    dependentes: Optional[str] = None
    imovel_ou_financiamento_ativo: Optional[str] = None  # sim, não
    restricao_cpf: Optional[str] = None  # sim, não, não informado
    entrada_disponivel: Optional[str] = None
    prazo_compra: Optional[str] = None  # até 3 meses, 3 a 6, 6 a 12, mais de 12

    # MCMV e Estoque
    pre_enquadramento_mcmv: Optional[str] = None
    imoveis_apresentados: list[str] = field(default_factory=list)
    imovel_maior_interesse: Optional[str] = None

    # Visita
    preferencia_visita: Optional[str] = None
    local_visita: Optional[str] = None
    status_visita: Optional[str] = None  # "a confirmar" (pela IA) ou "confirmada" (pelo vendedor)
    horario_visita_confirmado: Optional[str] = None
    lembrete_visita_enviado: bool = False

    # Classificação e Fluxo
    pontuacao: int = 0
    temperatura: str = "Frio"
    prazo_retorno_vendedor: str = "em até 48 horas"
    etapa: str = "em qualificação"  # em qualificação, qualificado, transferido, sem perfil, sem retorno
    motivo_descarte: Optional[str] = None
    duvidas_ou_objecoes: Optional[str] = None

    # Controle de Transbordo, Follow-up, SLA e LGPD
    vendedor_responsavel: str = field(default_factory=lambda: settings.VENDEDOR_PADRAO_NOME)
    vendedor_assumiu: bool = False
    data_hora_transferencia: Optional[str] = None
    sla_estourado: bool = False
    historico_redistribuicao: list[str] = field(default_factory=list)
    data_hora_ultima_interacao_cliente: Optional[str] = None
    etapas_followup_enviadas: list[str] = field(default_factory=list)
    opt_out_lgpd: bool = False
    resumo_conversa: Optional[str] = None
    historico_mensagens: list[dict] = field(default_factory=list)


class ServicoCRMAgendor:
    """Gerencia a persistência imediata dos leads e sincronização com o Agendor."""

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path: Path = storage_path or settings.CRM_STORAGE_PATH
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._leads: dict[str, RegistroLeadCRM] = {}
        from app.services.agendor_connector import AgendorCRMConnector

        self.agendor_api = AgendorCRMConnector()
        self._carregar()

    def _carregar(self) -> None:
        if not self.storage_path.exists():
            return
        try:
            raw = json.loads(self.storage_path.read_text(encoding="utf-8"))
            for tel, dados in raw.items():
                self._leads[tel] = RegistroLeadCRM(**dados)
        except Exception:
            self._leads = {}

    def _salvar(self) -> None:
        serializado = {tel: asdict(lead) for tel, lead in self._leads.items()}
        self.storage_path.write_text(
            json.dumps(serializado, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def obter_ou_criar_lead(
        self,
        telefone: str,
        origem: Optional[str] = None,
        campanha: Optional[str] = None,
    ) -> RegistroLeadCRM:
        tel_limpo = "".join(c for c in telefone if c.isdigit() or c == "+") or "padrao"
        if tel_limpo not in self._leads:
            self._leads[tel_limpo] = RegistroLeadCRM(
                telefone=tel_limpo,
                origem=origem or "WhatsApp direto",
                campanha=campanha,
            )
            self._salvar()
        elif origem and self._leads[tel_limpo].origem == "WhatsApp direto":
            self._leads[tel_limpo].origem = origem
            if campanha:
                self._leads[tel_limpo].campanha = campanha
            self._salvar()
        return self._leads[tel_limpo]

    def registrar_mensagem_historico(self, telefone: str, autor: str, texto: str) -> None:
        lead = self.obter_ou_criar_lead(telefone)
        agora_iso = datetime.now().isoformat()
        if autor == "lili" and not lead.data_hora_primeira_resposta:
            lead.data_hora_primeira_resposta = agora_iso
        if autor == "cliente":
            lead.data_hora_ultima_interacao_cliente = agora_iso
            # Quando o cliente volta a responder, reinicia a trilha de follow-up
            lead.etapas_followup_enviadas = []
            if lead.etapa == "sem retorno":
                lead.etapa = "em qualificação"
        lead.historico_mensagens.append(
            {"timestamp": agora_iso, "autor": autor, "texto": texto}
        )
        self._salvar()

    def atualizar_lead(self, telefone: str, **campos) -> dict:
        """
        Atualiza imediatamente os campos coletados do lead no CRM, recalcula
        o pré-enquadramento MCMV 2026 e a pontuação/temperatura.
        """
        lead = self.obter_ou_criar_lead(telefone)

        for chave, valor in campos.items():
            if valor is None:
                continue
            if chave == "imoveis_apresentados" and isinstance(valor, list):
                for cod in valor:
                    if cod not in lead.imoveis_apresentados:
                        lead.imoveis_apresentados.append(cod)
            elif hasattr(lead, chave):
                setattr(lead, chave, valor)

        # Atualiza pré-enquadramento MCMV
        enq = calcular_pre_enquadramento(
            renda_bruta=lead.renda_bruta_valor_aproximado,
            faixa_informada=lead.renda_bruta_familiar_faixa,
            cidade=lead.cidade,
        )
        if enq.get("faixa") and enq["faixa"] != "A definir":
            lead.pre_enquadramento_mcmv = enq["faixa"]

        # Recalcula pontuação determinística
        obrigatorias_preenchidas = all(
            bool(getattr(lead, c))
            for c in (
                "nome",
                "objetivo",
                "cidade",
                "quartos",
                "renda_bruta_familiar_faixa",
                "tipo_renda",
                "fgts_mais_3_anos",
                "dependentes",
                "imovel_ou_financiamento_ativo",
                "entrada_disponivel",
                "prazo_compra",
            )
        )
        tem_viabilidade = bool(
            (lead.entrada_disponivel and lead.entrada_disponivel.lower() not in ("não", "nao", "zero", "0", "nenhuma"))
            or (lead.fgts_mais_3_anos and "sim" in lead.fgts_mais_3_anos.lower())
        )
        tem_imovel_ativo = bool(
            lead.imovel_ou_financiamento_ativo
            and lead.imovel_ou_financiamento_ativo.strip().lower() in ("sim", "tenho", "possui")
        )
        aceitou_visita = bool(lead.preferencia_visita) or lead.etapa == "transferido"
        enquadrado_com_estoque = bool(
            lead.pre_enquadramento_mcmv
            and lead.pre_enquadramento_mcmv.startswith("Faixa")
        )

        score_info = calcular_pontuacao_e_temperatura(
            prazo_compra=lead.prazo_compra,
            pre_enquadrado_com_estoque=enquadrado_com_estoque,
            viabilidade_entrada_fgts_composicao=tem_viabilidade,
            aceitou_visita_ou_pediu_vendedor=aceitou_visita,
            respondeu_todas_obrigatorias=obrigatorias_preenchidas,
            imovel_ou_financiamento_ativo=tem_imovel_ativo,
            criterio_eliminatorio=lead.motivo_descarte,
        )
        lead.pontuacao = score_info["pontuacao"]
        lead.temperatura = score_info["temperatura"]
        lead.prazo_retorno_vendedor = score_info["prazo_retorno_vendedor"]

        if obrigatorias_preenchidas and lead.etapa == "em qualificação":
            lead.etapa = "qualificado"

        lead.resumo_conversa = self.gerar_resumo_6_linhas(lead)
        sync_agendor = self.agendor_api.sincronizar_lead(lead, lead.resumo_conversa)
        self._salvar()
        return {
            "status": "atualizado_no_agendor",
            "agendor_sync": {
                "operacao": sync_agendor["operacao"],
                "agendor_person_id": sync_agendor["agendor_person_id"],
                "agendor_deal_id": sync_agendor["agendor_deal_id"],
                "link_agendor": sync_agendor["link_agendor"],
            },
            "lead": asdict(lead),
            "classificacao": score_info,
            "pre_enquadramento": enq,
        }

    def registrar_preferencia_visita(
        self,
        telefone: str,
        opcoes_dia_periodo: str,
        local: str = "Stand / Plantão Central",
    ) -> dict:
        """
        Registra 2 ou 3 opções de dia/período e local sempre como 'visita a confirmar'.
        Nunca confirma a visita sozinha.
        """
        return self.atualizar_lead(
            telefone,
            preferencia_visita=opcoes_dia_periodo,
            local_visita=local,
            status_visita="a confirmar",
        )

    def gerar_resumo_6_linhas(self, lead: RegistroLeadCRM) -> str:
        """
        Gera o resumo padronizado de exatamente 6 linhas para o vendedor no Agendor
        (Seção 12 das Instruções Mestras).
        """
        linha_1 = f"Novo lead {lead.temperatura.upper()} ({lead.pontuacao} pts) – {lead.nome or 'Cliente'}"
        campanha_str = f", campanha {lead.campanha}" if lead.campanha else ""
        linha_2 = f"Origem: {lead.origem}{campanha_str}"
        quartos_str = f"{lead.quartos} quartos" if lead.quartos else "quartos a definir"
        linha_3 = (
            f"Objetivo: {lead.objetivo or 'morar'}, 1º imóvel: {lead.primeiro_imovel or 'sim'} | "
            f"{lead.tipo_imovel or 'Imóvel'} {quartos_str} | {lead.cidade or 'Região aberta'}"
        )
        linha_4 = (
            f"Renda bruta: {lead.renda_bruta_familiar_faixa or 'a confirmar'} ({lead.tipo_renda or 'a confirmar'}) | "
            f"Pré-enquadramento: {lead.pre_enquadramento_mcmv or 'em análise'}"
        )
        linha_5 = (
            f"FGTS: {lead.fgts_mais_3_anos or 'não informado'} | "
            f"Entrada: {lead.entrada_disponivel or 'não informada'} | "
            f"CPF: {lead.restricao_cpf or 'sem restrição informada'}"
        )
        visita_ou_obs = (
            f"Visita: {lead.preferencia_visita} ({lead.status_visita or 'a confirmar'})"
            if lead.preferencia_visita
            else f"Obs/Dúvida: {lead.duvidas_ou_objecoes or 'Aguardando simulação/atendimento'}"
        )
        linha_6 = (
            f"Prazo: {lead.prazo_compra or 'a definir'} | "
            f"Interesse: {lead.imovel_maior_interesse or ', '.join(lead.imoveis_apresentados) or 'Estoque compatível'} | "
            f"{visita_ou_obs}"
        )
        return "\n".join([linha_1, linha_2, linha_3, linha_4, linha_5, linha_6])

    def transferir_para_vendedor(
        self,
        telefone: str,
        motivo_transferencia: str,
        duvidas_ou_objecoes: Optional[str] = None,
        vendedor: Optional[str] = None,
    ) -> dict:
        """
        Grava o resumo de 6 linhas no CRM, atualiza a etapa para 'transferido'
        e retorna os dados exatos (nome do vendedor e SLA) para informar ao cliente.
        """
        lead = self.obter_ou_criar_lead(telefone)
        if duvidas_ou_objecoes:
            lead.duvidas_ou_objecoes = duvidas_ou_objecoes
        elif motivo_transferencia:
            lead.duvidas_ou_objecoes = motivo_transferencia

        if vendedor:
            lead.vendedor_responsavel = vendedor

        lead.etapa = "transferido"
        if not lead.data_hora_transferencia:
            lead.data_hora_transferencia = datetime.now().isoformat()
        self.atualizar_lead(telefone)
        lead.resumo_conversa = self.gerar_resumo_6_linhas(lead)
        self._salvar()

        return {
            "status": "transferido_ao_vendedor",
            "vendedor_responsavel": lead.vendedor_responsavel,
            "prazo_retorno": lead.prazo_retorno_vendedor,
            "temperatura": lead.temperatura,
            "pontuacao": lead.pontuacao,
            "resumo_6_linhas_crm": lead.resumo_conversa,
            "mensagem_modelo_cliente": (
                f"Prontinho, {lead.nome or ''}! Passei tudo pro {lead.vendedor_responsavel}, "
                f"que vai falar com você {lead.prazo_retorno_vendedor}. O melhor da construção te espera!"
            ).replace(" ,", ","),
        }

    def encerrar_sem_perfil(self, telefone: str, motivo: str) -> dict:
        """Registra o motivo eliminatório no CRM e marca como 'sem perfil'."""
        lead = self.obter_ou_criar_lead(telefone)
        lead.motivo_descarte = motivo
        lead.etapa = "sem perfil"
        self.atualizar_lead(telefone, motivo_descarte=motivo)
        return {
            "status": "encerrado_sem_perfil",
            "motivo_registrado": motivo,
            "temperatura": lead.temperatura,
        }

    def registrar_opt_out_lgpd(self, telefone: str) -> dict:
        """Atende imediatamente ao pedido de parar de receber mensagens (LGPD)."""
        lead = self.obter_ou_criar_lead(telefone)
        lead.opt_out_lgpd = True
        lead.etapa = "opt-out (LGPD)"
        lead.motivo_descarte = "Solicitou opt-out (parar de receber mensagens - LGPD)"
        self._salvar()
        return {
            "status": "opt_out_confirmado",
            "mensagem": "Registrado no CRM. Envios futuros interrompidos imediatamente.",
        }

    def definir_controle_vendedor(self, telefone: str, assumir: bool) -> dict:
        """
        Botão que desliga/religa a ação da IA quando o vendedor assume ou devolve o contato.
        """
        lead = self.obter_ou_criar_lead(telefone)
        lead.vendedor_assumiu = assumir
        self._salvar()
        return {
            "telefone": lead.telefone,
            "vendedor_assumiu": lead.vendedor_assumiu,
            "ia_ativa": not lead.vendedor_assumiu,
        }

    def listar_todos_leads(self) -> list[dict]:
        """Retorna a lista de todos os leads registrados para o painel de gestão e relatórios."""
        self._carregar()
        return [asdict(lead) for lead in self._leads.values()]

