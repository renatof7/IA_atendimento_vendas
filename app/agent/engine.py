"""
Motor Principal da Lili (Engine de Conversação + Anthropic Claude Tool Use + CRM em Tempo Real).
Integra:
- Anthropic Claude SDK (`anthropic`) com ciclo completo de Tool Use (`stop_reason == "tool_use"`)
- Motor Conversacional Determinístico de Pré-Vendas (para execução local imediata quando ANTHROPIC_API_KEY não estiver configurada)
- Guardrails estritos de comunicação, MCMV 2026, Base XML e CRM Agendor.
"""

import json
import logging
import re
import urllib.request
import urllib.error
from dataclasses import asdict
from typing import Optional

from app.config import settings, BASE_DIR
from app.domain.mcmv import calcular_pre_enquadramento, _normalizar_texto
from app.services.xml_catalog import CatalogoImoveisXML
from app.services.crm_service import ServicoCRMAgendor, RegistroLeadCRM
from app.services.institucional_service import ServicoInstitucional
from app.agent.claude_tools import CLAUDE_TOOLS_SCHEMA
from app.agent.groq_tools import GROQ_TOOLS_SCHEMA
from app.agent.guardrails import (
    detectar_prompt_injection,
    detectar_opt_out_lgpd,
    detectar_envio_documento_cpf,
    aplicar_guardrails_resposta,
)

logger = logging.getLogger("lili.engine")


def carregar_system_prompt() -> str:
    """Carrega o System Prompt oficial do arquivo GEMINI.md na raiz do projeto."""
    gemini_md = BASE_DIR / "GEMINI.md"
    if gemini_md.exists():
        return gemini_md.read_text(encoding="utf-8")
    return "Você é a Lili, assistente virtual de pré-vendas da Construtora Demo."


class MotorLili:
    """Orquestrador central de atendimento da Lili com integração Anthropic Claude."""

    def __init__(
        self,
        catalogo: Optional[CatalogoImoveisXML] = None,
        crm: Optional[ServicoCRMAgendor] = None,
        institucional: Optional[ServicoInstitucional] = None,
    ):
        self.catalogo = catalogo or CatalogoImoveisXML()
        self.crm = crm or ServicoCRMAgendor()
        self.institucional = institucional or ServicoInstitucional()
        self.system_prompt = carregar_system_prompt()

    def executar_tool_claude(
        self,
        telefone: str,
        tool_name: str,
        tool_input: dict,
        lead: RegistroLeadCRM,
    ) -> dict:
        """
        Executa uma ferramenta solicitada pelo Claude via `tool_use` e retorna o dicionário de resultado.
        """
        if tool_name == "buscar_imoveis":
            res = self.catalogo.buscar_imoveis(
                cidade=tool_input.get("cidade") or lead.cidade,
                bairro=tool_input.get("bairro"),
                tipo=tool_input.get("tipo") or lead.tipo_imovel,
                quartos=tool_input.get("quartos") or lead.quartos,
                valor_maximo=tool_input.get("valor_maximo"),
                faixa_mcmv=tool_input.get("faixa_mcmv") or lead.pre_enquadramento_mcmv,
                renda_bruta=lead.renda_bruta_valor_aproximado,
                status_entrega=tool_input.get("status_entrega"),
            )
            imoveis = res.get("imoveis", [])
            if imoveis:
                codigos = [im["codigo"] for im in imoveis]
                self.crm.atualizar_lead(
                    telefone,
                    imoveis_apresentados=codigos,
                    imovel_maior_interesse=imoveis[0]["nome"],
                )
            return res

        if tool_name == "detalhar_imovel":
            detalhe = self.catalogo.detalhar_imovel(tool_input.get("codigo", ""))
            return detalhe or {"erro": "Imóvel não encontrado ou sem disponibilidade."}

        if tool_name == "atualizar_lead":
            return self.crm.atualizar_lead(telefone, **tool_input)

        if tool_name == "calcular_pre_enquadramento_mcmv":
            return calcular_pre_enquadramento(
                renda_bruta=tool_input.get("renda_bruta") or lead.renda_bruta_valor_aproximado,
                faixa_informada=tool_input.get("faixa_informada") or lead.renda_bruta_familiar_faixa,
                cidade=tool_input.get("cidade") or lead.cidade,
                valor_imovel=tool_input.get("valor_imovel"),
                imovel_novo=tool_input.get("imovel_novo", True),
            )

        if tool_name == "registrar_preferencia_visita":
            return self.crm.registrar_preferencia_visita(
                telefone=telefone,
                opcoes_dia_periodo=tool_input.get("opcoes_dia_periodo", ""),
                local=tool_input.get("local", "Stand / Plantão Central"),
            )

        if tool_name == "transferir_para_vendedor":
            return self.crm.transferir_para_vendedor(
                telefone=telefone,
                motivo_transferencia=tool_input.get("motivo_transferencia", "Solicitação de atendimento"),
                duvidas_ou_objecoes=tool_input.get("duvidas_ou_objecoes"),
            )

        if tool_name == "encerrar_sem_perfil":
            return self.crm.encerrar_sem_perfil(
                telefone=telefone,
                motivo=tool_input.get("motivo", "Sem perfil"),
            )

        if tool_name == "consultar_informacoes_institucionais":
            return self.institucional.consultar_topico(
                topico=tool_input.get("topico", "faq"),
                cidade=tool_input.get("cidade") or lead.cidade,
            )

        return {"erro": f"Ferramenta desconhecida: {tool_name}"}

    # Alias para compatibilidade com Groq e Claude
    executar_tool = executar_tool_claude

    def processar_mensagem(
        self,
        telefone: str,
        mensagem: str,
        origem: Optional[str] = None,
        campanha: Optional[str] = None,
    ) -> dict:
        """
        Processa a mensagem recebida do cliente pelo WhatsApp:
        1. Verifica se o vendedor assumiu o atendimento (botão de desligamento manual)
        2. Verifica se o cliente pediu opt-out (LGPD) ou enviou prompt injection
        3. Extrai entidades e grava no CRM em tempo real
        4. Executa Claude com Tool Use (ou fluxo conversacional determinístico local)
        5. Aplica os Guardrails de comunicação na resposta da Lili.
        """
        lead = self.crm.obter_ou_criar_lead(telefone, origem=origem, campanha=campanha)
        self.crm.registrar_mensagem_historico(telefone, "cliente", mensagem)
        tools_executadas: list[dict] = []

        # 1. Se o vendedor já assumiu o contato (botão manual desligou a IA)
        if lead.vendedor_assumiu:
            return {
                "ia_ativa": False,
                "provedor_ia": "pausado_pelo_vendedor",
                "resposta_lili": None,
                "motivo": f"Atendimento assumido pelo vendedor {lead.vendedor_responsavel}. IA pausada neste contato.",
                "tools_executadas": [],
                "lead_crm": asdict(lead),
            }

        # 2. Pedido de Opt-Out (LGPD)
        if detectar_opt_out_lgpd(mensagem):
            res_opt = self.crm.registrar_opt_out_lgpd(telefone)
            tools_executadas.append({"tool": "registrar_opt_out_lgpd", "resultado": res_opt})
            resposta = aplicar_guardrails_resposta(
                f"Combinado{', ' + lead.nome if lead.nome else ''}! Já registrei seu pedido aqui e "
                "você não vai mais receber nossas mensagens. Precisando no futuro, estaremos à disposição."
            )
            self.crm.registrar_mensagem_historico(telefone, "lili", resposta)
            return {
                "ia_ativa": True,
                "provedor_ia": "guardrail_lgpd",
                "resposta_lili": resposta,
                "tools_executadas": tools_executadas,
                "lead_crm": asdict(self.crm.obter_ou_criar_lead(telefone)),
            }

        # 3. Proteção contra Prompt Injection
        if detectar_prompt_injection(mensagem):
            resposta = aplicar_guardrails_resposta(
                "Eu sou a Lili, assistente virtual de pré-vendas, e sigo as regras oficiais do nosso atendimento 😊\n"
                "Me conta: você tá buscando um imóvel pra morar ou pra investir?"
            )
            self.crm.registrar_mensagem_historico(telefone, "lili", resposta)
            return {
                "ia_ativa": True,
                "provedor_ia": "guardrail_security",
                "resposta_lili": resposta,
                "tools_executadas": [{"tool": "bloqueio_prompt_injection", "status": "bloqueado"}],
                "lead_crm": asdict(lead),
            }

        # 4. Proteção contra recebimento de número de CPF/documentos no WhatsApp
        aviso_cpf_numero = ""
        if detectar_envio_documento_cpf(mensagem):
            aviso_cpf_numero = (
                "Por segurança, não precisamos do número do CPF aqui pelo WhatsApp — "
                "os documentos são entregues só ao vendedor na hora da simulação, tá bom?\n"
            )

        # 5. Extração de informações em tempo real da fala do cliente
        campos_extraidos = self._extrair_dados_mensagem(mensagem, lead)
        if campos_extraidos:
            res_crm = self.crm.atualizar_lead(telefone, **campos_extraidos)
            tools_executadas.append(
                {
                    "tool": "atualizar_lead",
                    "argumentos": campos_extraidos,
                    "resultado": {
                        "pontuacao": res_crm["classificacao"]["pontuacao"],
                        "temperatura": res_crm["classificacao"]["temperatura"],
                        "pre_enquadramento": res_crm["pre_enquadramento"].get("faixa"),
                    },
                }
            )
            lead = self.crm.obter_ou_criar_lead(telefone)

        # 6. Gera resposta via GroqCloud (Llama/Qwen), Anthropic Claude ou Motor Local
        provedor_usado = "local_deterministico"
        if settings.GROQ_API_KEY:
            resposta_bruta, tools_groq, erro_groq = self._gerar_com_groq(telefone, mensagem, lead)
            tools_executadas.extend(tools_groq)
            if not erro_groq:
                provedor_usado = f"groq:{settings.GROQ_MODEL}"
            else:
                provedor_usado = f"fallback_local (Groq: {erro_groq})"
        elif settings.ANTHROPIC_API_KEY:
            resposta_bruta, tools_claude = self._gerar_com_claude(telefone, mensagem, lead)
            tools_executadas.extend(tools_claude)
            provedor_usado = f"anthropic:{settings.ANTHROPIC_MODEL}"
        else:
            resposta_bruta, tools_locais = self._gerar_fluxo_conversacional(telefone, mensagem, lead)
            tools_executadas.extend(tools_locais)

        if aviso_cpf_numero:
            resposta_bruta = aviso_cpf_numero + resposta_bruta

        resposta_final = aplicar_guardrails_resposta(resposta_bruta)
        self.crm.registrar_mensagem_historico(telefone, "lili", resposta_final)

        lead_atualizado = self.crm.obter_ou_criar_lead(telefone)
        return {
            "ia_ativa": True,
            "provedor_ia": provedor_usado,
            "resposta_lili": resposta_final,
            "tools_executadas": tools_executadas,
            "lead_crm": asdict(lead_atualizado),
        }

    def _gerar_com_groq(
        self,
        telefone: str,
        mensagem: str,
        lead: RegistroLeadCRM,
    ) -> tuple[str, list[dict], Optional[str]]:
        """
        Executa chamada de inferência à API GroqCloud com ciclo completo de Tool Calling nativo.
        Utiliza requests com fallback inteligente de modelos e logging em tempo real.
        """
        import requests

        tools_chamadas: list[dict] = []
        try:
            # 1. Monta histórico de mensagens no formato role/content
            mensagens_groq: list[dict] = []
            for item in lead.historico_mensagens[-12:]:
                role = "user" if item["autor"] == "cliente" else "assistant"
                mensagens_groq.append({"role": role, "content": item["texto"]})

            if not mensagens_groq or mensagens_groq[-1]["role"] != "user":
                mensagens_groq.append({"role": "user", "content": mensagem})

            estado_crm_resumo = {
                k: v
                for k, v in asdict(lead).items()
                if k != "historico_mensagens" and v is not None
            }
            system_instruction = (
                f"{self.system_prompt}\n\n"
                f"## ESTADO ATUAL DO LEAD NO CRM AGENDOR (NÃO REPERGUNTE O QUE JÁ ESTÁ PREENCHIDO):\n"
                f"{json.dumps(estado_crm_resumo, ensure_ascii=False, indent=2)}\n"
                f"Horário de plantão: {settings.HORARIOS_PLANTAO}\n"
                f"Vendedor responsável: {lead.vendedor_responsavel} (SLA atual: {lead.prazo_retorno_vendedor})\n"
                f"REGRAS CRÍTICAS: Responda em no máximo 3 linhas, no máximo 2 perguntas por mensagem. "
                f"Nunca prometa aprovação de crédito nem valor exato de parcelas. O WhatsApp vende a visita e a simulação presencial!"
            )

            mensagens_envio: list[dict] = [{"role": "system", "content": system_instruction}] + mensagens_groq

            endpoint = f"{settings.GROQ_BASE_URL}/chat/completions"
            headers = {
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json",
                "User-Agent": "Lili-IA/2.0 (Windows NT 10.0; Win64; x64)",
            }

            modelo_ativo = settings.GROQ_MODEL
            print(f"[Lili GroqCloud] Chamando IA ({modelo_ativo}) para mensagem: '{mensagem[:40]}'...", flush=True)

            # Ciclo de Tool Calling da Groq (até 4 iterações de ferramentas por turno)
            for iteracao in range(4):
                payload = {
                    "model": modelo_ativo,
                    "messages": mensagens_envio,
                    "tools": GROQ_TOOLS_SCHEMA,
                    "tool_choice": "auto",
                    "temperature": settings.GROQ_TEMPERATURE,
                    "max_tokens": settings.GROQ_MAX_TOKENS,
                }

                resp = requests.post(endpoint, headers=headers, json=payload, timeout=20)

                # Se o modelo configurado retornar 404 (model_not_found), tenta automaticamente o modelo padrão disponível
                if resp.status_code == 404 and modelo_ativo != "qwen/qwen3.8-27b":
                    print(f"[Lili GroqCloud] Modelo {modelo_ativo} não encontrado. Alternando para qwen/qwen3.8-27b...", flush=True)
                    modelo_ativo = "qwen/qwen3.8-27b"
                    payload["model"] = modelo_ativo
                    resp = requests.post(endpoint, headers=headers, json=payload, timeout=20)

                if resp.status_code != 200:
                    erro_msg = f"HTTP {resp.status_code}: {resp.text[:150]}"
                    print(f"[Lili GroqCloud ERRO] {erro_msg}", flush=True)
                    resp_fluxo, tools_loc = self._gerar_fluxo_conversacional(telefone, mensagem, lead)
                    return resp_fluxo, tools_chamadas + tools_loc, erro_msg

                resp_data = resp.json()
                choices = resp_data.get("choices", [])
                if not choices:
                    break

                choice = choices[0]
                msg_resposta = choice.get("message", {})
                tool_calls = msg_resposta.get("tool_calls", [])

                if not tool_calls:
                    conteudo = msg_resposta.get("content", "")
                    if conteudo:
                        print(f"[Lili GroqCloud] Resposta gerada com sucesso pela IA ({len(conteudo)} chars).", flush=True)
                        return conteudo, tools_chamadas, None
                    break

                # Adiciona a resposta com tool_calls ao contexto
                mensagens_envio.append(msg_resposta)

                # Processa cada tool_call solicitada pela IA
                for tc in tool_calls:
                    tc_id = tc.get("id", "")
                    func = tc.get("function", {})
                    t_name = func.get("name", "")
                    args_raw = func.get("arguments", "{}")
                    try:
                        t_args = json.loads(args_raw) if isinstance(args_raw, str) else (args_raw or {})
                    except Exception:
                        t_args = {}

                    print(f"[Lili GroqCloud Tool] IA executou ferramenta: {t_name}({t_args})", flush=True)
                    lead_atual = self.crm.obter_ou_criar_lead(telefone)
                    resultado_tool = self.executar_tool(
                        telefone=telefone,
                        tool_name=t_name,
                        tool_input=t_args,
                        lead=lead_atual,
                    )
                    tools_chamadas.append(
                        {
                            "tool": t_name,
                            "argumentos": t_args,
                            "resultado": resultado_tool,
                        }
                    )
                    mensagens_envio.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc_id,
                            "name": t_name,
                            "content": json.dumps(resultado_tool, ensure_ascii=False),
                        }
                    )

        except Exception as exc:
            erro_str = str(exc)
            print(f"[Lili GroqCloud Falha]: {erro_str}. Acionando fallback conversacional.", flush=True)
            logger.warning(f"GroqCloud falhou ou offline ({exc}). Acionando fallback conversacional.")
            resp_fluxo, tools_loc = self._gerar_fluxo_conversacional(telefone, mensagem, lead)
            return resp_fluxo, tools_chamadas + tools_loc, erro_str

        resp_fluxo, tools_loc = self._gerar_fluxo_conversacional(telefone, mensagem, lead)
        return resp_fluxo, tools_chamadas + tools_loc, None

    def _gerar_com_claude(
        self,
        telefone: str,
        mensagem: str,
        lead: RegistroLeadCRM,
    ) -> tuple[str, list[dict]]:
        """
        Executa chamada à API Anthropic Claude (`messages.create`) com suporte completo
        a múltiplos ciclos de Tool Use (`stop_reason == "tool_use"` -> `tool_result`).
        """
        tools_chamadas: list[dict] = []
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

            # Monta histórico de mensagens no formato user/assistant do Claude
            mensagens_claude: list[dict] = []
            for item in lead.historico_mensagens[-12:]:
                role = "user" if item["autor"] == "cliente" else "assistant"
                texto = item["texto"]
                if mensagens_claude and mensagens_claude[-1]["role"] == role:
                    mensagens_claude[-1]["content"] += f"\n{texto}"
                else:
                    mensagens_claude.append({"role": role, "content": texto})

            if not mensagens_claude or mensagens_claude[-1]["role"] != "user":
                mensagens_claude.append({"role": "user", "content": mensagem})

            estado_crm_resumo = {
                k: v
                for k, v in asdict(lead).items()
                if k != "historico_mensagens" and v is not None
            }
            system_instruction = (
                f"{self.system_prompt}\n\n"
                f"## ESTADO ATUAL DO LEAD NO CRM AGENDOR (NÃO REPERGUNTE O QUE JÁ ESTÁ PREENCHIDO):\n"
                f"{json.dumps(estado_crm_resumo, ensure_ascii=False, indent=2)}\n"
                f"Horário de plantão: {settings.HORARIOS_PLANTAO}\n"
                f"Vendedor responsável: {lead.vendedor_responsavel} (SLA atual: {lead.prazo_retorno_vendedor})"
            )

            # Ciclo de Tool Use do Claude (até 4 iterações de ferramentas por turno)
            for _ in range(4):
                response = client.messages.create(
                    model=settings.ANTHROPIC_MODEL,
                    max_tokens=settings.ANTHROPIC_MAX_TOKENS,
                    temperature=0.3,
                    system=system_instruction,
                    tools=CLAUDE_TOOLS_SCHEMA,
                    messages=mensagens_claude,
                )

                if response.stop_reason != "tool_use":
                    textos = [
                        block.text
                        for block in response.content
                        if getattr(block, "type", None) == "text"
                    ]
                    if textos:
                        return "\n".join(textos), tools_chamadas
                    break

                # Processa cada bloco tool_use solicitado pelo Claude
                mensagens_claude.append({"role": "assistant", "content": response.content})
                blocos_tool_result: list[dict] = []

                for block in response.content:
                    if getattr(block, "type", None) == "tool_use":
                        t_name = block.name
                        t_input = block.input or {}
                        lead_atual = self.crm.obter_ou_criar_lead(telefone)
                        resultado_tool = self.executar_tool_claude(
                            telefone=telefone,
                            tool_name=t_name,
                            tool_input=t_input,
                            lead=lead_atual,
                        )
                        tools_chamadas.append(
                            {
                                "tool": t_name,
                                "argumentos": t_input,
                                "resultado": resultado_tool,
                            }
                        )
                        blocos_tool_result.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps(resultado_tool, ensure_ascii=False),
                            }
                        )

                mensagens_claude.append({"role": "user", "content": blocos_tool_result})

        except Exception as exc:
            logger.warning(f"Fallback para motor conversacional local acionado ({exc})")

        return self._gerar_fluxo_conversacional(telefone, mensagem, lead)

    def _extrair_dados_mensagem(self, mensagem: str, lead: RegistroLeadCRM) -> dict:
        """Extrai campos de qualificação presentes na mensagem natural do cliente."""
        extraidos: dict = {}
        msg_norm = _normalizar_texto(mensagem)

        # Nome (ex: "sou o Renato", "meu nome é Maria", "aqui é a Ana")
        if not lead.nome:
            m_nome = re.search(
                r"(?:sou o|sou a|meu nome [eé]|me chamo|aqui [eé] o|aqui [eé] a|fala com o|fala com a)\s+([A-ZÀ-Úa-zà-ú]{2,20})",
                mensagem,
                re.IGNORECASE,
            )
            if m_nome:
                extraidos["nome"] = m_nome.group(1).strip().title()
            elif len(mensagem.strip().split()) == 1 and len(mensagem.strip()) >= 3:
                palavra = mensagem.strip()
                if palavra.isalpha() and palavra.lower() not in (
                    "oi",
                    "ola",
                    "olá",
                    "sim",
                    "nao",
                    "não",
                    "casa",
                    "apto",
                ):
                    extraidos["nome"] = palavra.title()

        # Objetivo e primeiro imóvel
        if "investir" in msg_norm or "investimento" in msg_norm:
            extraidos["objetivo"] = "investir"
        elif any(k in msg_norm for k in ("morar", "sair do aluguel", "meu primeiro", "comprar")):
            if not lead.objetivo:
                extraidos["objetivo"] = "morar"
        if "primeiro imovel" in msg_norm or "1o imovel" in msg_norm or "nunca financiei" in msg_norm:
            extraidos["primeiro_imovel"] = "Sim"
            extraidos["imovel_ou_financiamento_ativo"] = "Não"

        # Cidade
        if "tubarao" in msg_norm:
            extraidos["cidade"] = "Tubarão"
        elif "capivari" in msg_norm:
            extraidos["cidade"] = "Capivari de Baixo"
        elif "pescaria" in msg_norm or "brava" in msg_norm:
            extraidos["cidade"] = "Pescaria Brava"
        elif any(k in msg_norm for k in ("qualquer lugar", "qualquer cidade", "tanto faz", "aberto")):
            extraidos["cidade"] = "Qualquer (Tubarão, Capivari de Baixo, Pescaria Brava)"

        # Tipo de imóvel
        if any(k in msg_norm for k in ("apartamento", "apto", "ap ")):
            extraidos["tipo_imovel"] = "Apartamento"
        elif "casa" in msg_norm:
            extraidos["tipo_imovel"] = "Casa"

        # Quartos
        m_quartos = re.search(r"(\d)\s*(?:quarto|dormit[oó]rio)", msg_norm)
        if m_quartos:
            extraidos["quartos"] = int(m_quartos.group(1))
        elif "dois quartos" in msg_norm:
            extraidos["quartos"] = 2
        elif "tres quartos" in msg_norm:
            extraidos["quartos"] = 3

        # Renda bruta / Faixa
        if "faixa 1" in msg_norm or "primeira faixa" in msg_norm:
            extraidos["renda_bruta_familiar_faixa"] = "Faixa 1 (a partir de R$ 1.900)"
            extraidos["renda_bruta_valor_aproximado"] = 2500.0
        elif "segunda faixa" in msg_norm or "faixa 3" in msg_norm or "5 mil a 9" in msg_norm or "5 a 9" in msg_norm:
            extraidos["renda_bruta_familiar_faixa"] = "Faixa 3 (R$ 5.000,01 a R$ 9.600)"
            extraidos["renda_bruta_valor_aproximado"] = 6500.0
        elif "faixa 2" in msg_norm or "ate 5 mil" in msg_norm or "ate 5000" in msg_norm:
            extraidos["renda_bruta_familiar_faixa"] = "Faixa 2 (até R$ 5.000)"
            extraidos["renda_bruta_valor_aproximado"] = 4200.0
        elif "faixa 4" in msg_norm or "9600 a 13" in msg_norm or "10 mil de renda" in msg_norm:
            extraidos["renda_bruta_familiar_faixa"] = "Faixa 4 (R$ 9.600,01 a R$ 13.000)"
            extraidos["renda_bruta_valor_aproximado"] = 11000.0
        else:
            m_renda = re.search(
                r"(?:renda|ganho|recebo|somando da|salario)\D{0,15}?(\d{1,2}(?:[\.,]\d{3})|\d{4,5}|\d{1,2}\s*mil)",
                msg_norm,
            )
            if m_renda:
                bruto_txt = m_renda.group(1)
                if "mil" in bruto_txt:
                    num = float(re.sub(r"\D", "", bruto_txt)) * 1000.0
                else:
                    num = float(bruto_txt.replace(".", "").replace(",", "."))
                extraidos["renda_bruta_valor_aproximado"] = num
                enq = calcular_pre_enquadramento(renda_bruta=num, cidade=lead.cidade)
                extraidos["renda_bruta_familiar_faixa"] = f"R$ {num:,.2f} ({enq.get('faixa')})"

        # Tipo de renda
        if any(k in msg_norm for k in ("carteira assinada", "clt", "registrado")):
            extraidos["tipo_renda"] = "Formal (CLT)"
        elif any(k in msg_norm for k in ("autonomo", "pj", "mei", "empresario", "conta propria")):
            extraidos["tipo_renda"] = "Autônomo / PJ"
        elif "um pouco de cada" in msg_norm or "mista" in msg_norm:
            extraidos["tipo_renda"] = "Mista"

        # FGTS
        if "fgts" in msg_norm:
            if any(k in msg_norm for k in ("tenho fgts", "sim", "uso fgts", "mais de 3 anos")):
                extraidos["fgts_mais_3_anos"] = "Sim"
            elif any(k in msg_norm for k in ("nao tenho fgts", "sem fgts")):
                extraidos["fgts_mais_3_anos"] = "Não"

        # Dependentes
        if "morar sozinho" in msg_norm or "so eu" in msg_norm:
            extraidos["dependentes"] = "Nenhum (vai morar sozinho)"
        elif any(k in msg_norm for k in ("esposa", "marido", "filho", "filha", "familia", "noiva", "noivo")):
            extraidos["dependentes"] = "Família / Cônjuge"

        # Entrada disponível
        m_entrada = re.search(
            r"(\d{1,3}\s*mil|\d{2,3}[\.,]\d{3})\s*(?:pra entrada|de entrada|guardado|separado)",
            msg_norm,
        )
        if not m_entrada:
            m_entrada = re.search(
                r"(?:tenho|entrada de)\s*(?:r\$\s*)?(\d{1,3}\s*mil|\d{2,3}[\.,]\d{3})",
                msg_norm,
            )
        if m_entrada:
            extraidos["entrada_disponivel"] = f"R$ {m_entrada.group(1)}"

        # Restrição no CPF
        if any(k in msg_norm for k in ("fies", "serasa", "spc", "pendencia", "restricao", "nome sujo")):
            extraidos["restricao_cpf"] = f"Sim ({mensagem.strip()})"
        elif any(k in msg_norm for k in ("cpf limpo", "sem pendencia", "sem restricao", "tudo certinho no cpf")):
            extraidos["restricao_cpf"] = "Não"

        # Prazo de compra
        if any(
            k in msg_norm
            for k in ("ate 3 meses", "imediato", "ja", "agora", "mes que vem", "fevereiro", "urgente")
        ):
            extraidos["prazo_compra"] = "até 3 meses"
        elif any(k in msg_norm for k in ("3 a 6", "6 meses", "meio do ano")):
            extraidos["prazo_compra"] = "3 a 6 meses"
        elif any(k in msg_norm for k in ("6 a 12", "1 ano", "final do ano")):
            extraidos["prazo_compra"] = "6 a 12 meses"

        # Aceitação de "prefiro não informar"
        if "prefiro nao informar" in msg_norm or "nao quero falar" in msg_norm:
            if not lead.renda_bruta_familiar_faixa:
                extraidos["renda_bruta_familiar_faixa"] = "Prefiro não informar"
            elif not lead.restricao_cpf:
                extraidos["restricao_cpf"] = "Não informado"

        return extraidos

    def _gerar_fluxo_conversacional(
        self,
        telefone: str,
        mensagem: str,
        lead: RegistroLeadCRM,
    ) -> tuple[str, list[dict]]:
        """
        Conduz o atendimento seguindo rigorosamente as 7 etapas do Mapa de Atendimento,
        tratamento de objeções, busca obrigatória no XML e regras de transbordo.
        """
        msg_norm = _normalizar_texto(mensagem)
        tools_chamadas: list[dict] = []
        nome_tratamento = f", {lead.nome}" if lead.nome else ""

        # A. Transparência sobre ser IA / Robô
        if any(k in msg_norm for k in ("voce e robo", "e uma ia", "inteligencia artificial", "atendente humano")):
            if "falar com uma pessoa" not in msg_norm and "atendente humano" not in msg_norm:
                return (
                    f"Sim{nome_tratamento}! Eu sou a Lili, a inteligência artificial da Construtora Demo, "
                    "e um vendedor do nosso time também vai acompanhar todo o seu atendimento 😊\n"
                    "Me conta: em qual cidade você pensa em morar e de quantos quartos precisa?",
                    tools_chamadas,
                )

        # B. Critérios Eliminatórios e Canais Específicos (Seção 11 e 13)
        if any(k in msg_norm for k in ("quero alugar", "para alugar", "tem para locacao", "procuro aluguel")):
            res_desc = self.crm.encerrar_sem_perfil(telefone, "locacao")
            tools_chamadas.append({"tool": "encerrar_sem_perfil", "resultado": res_desc})
            return (
                f"Que pena{nome_tratamento}! Aqui nós trabalhamos exclusivamente com a venda "
                "de imóveis próprios e não operamos com locação.\n"
                "Se no futuro você quiser ver como sair do aluguel pelo Minha Casa, Minha Vida, pode contar comigo!",
                tools_chamadas,
            )

        if any(k in msg_norm for k in ("segunda via de boleto", "2a via de boleto", "assistencia tecnica", "ja sou cliente", "meu contrato ativo")):
            info_pv = self.institucional.consultar_topico("pos_venda")
            tools_chamadas.append({"tool": "consultar_informacoes_institucionais", "resultado": info_pv})
            canal_pv = info_pv["dados"]["contato"]
            return (
                f"Oi{nome_tratamento}! Como você já é nosso cliente, esse atendimento é feito direto pela nossa Central de Relacionamento e Pós-Venda 😊\n"
                f"É só entrar em contato pelo canal: {canal_pv} que a equipe resolve rapidinho pra você!",
                tools_chamadas,
            )

        if any(k in msg_norm for k in ("sou corretor", "sou de imobiliaria", "parceria comercial", "cadastrar imobiliaria")):
            info_parc = self.institucional.consultar_topico("parcerias")
            res_desc = self.crm.encerrar_sem_perfil(telefone, "corretor_parceiro")
            tools_chamadas.append({"tool": "consultar_informacoes_institucionais", "resultado": info_parc})
            tools_chamadas.append({"tool": "encerrar_sem_perfil", "resultado": res_desc})
            return (
                f"Que bacana seu interesse em ser nosso parceiro comercial{nome_tratamento}! 😊\n"
                f"Pra credenciamento e tabelas de parcerias, fale direto com nossa Coordenação pelo e-mail: {info_parc['dados']['contato']}.",
                tools_chamadas,
            )

        if any(k in msg_norm for k in ("enviar curriculo", "trabalhe conosco", "sou fornecedor", "vender material", "imprensa")):
            info_forn = self.institucional.consultar_topico("fornecedor")
            res_desc = self.crm.encerrar_sem_perfil(telefone, "imprensa_fornecedor_curriculo")
            tools_chamadas.append({"tool": "consultar_informacoes_institucionais", "resultado": info_forn})
            tools_chamadas.append({"tool": "encerrar_sem_perfil", "resultado": res_desc})
            return (
                f"Obrigada pelo contato{nome_tratamento}! 😊\n"
                f"Como aqui é o canal exclusivo de pré-vendas de imóveis, você pode encaminhar direto para o setor responsável: {info_forn['dados']['contato']}.",
                tools_chamadas,
            )

        # B2. Dúvidas Institucionais (Documentação Básica e Endereço/Horário de Plantão)
        if any(k in msg_norm for k in ("quais documentos", "que documentos", "documentacao necessaria", "preciso levar")):
            info_doc = self.institucional.consultar_topico("documentacao")
            tools_chamadas.append({"tool": "consultar_informacoes_institucionais", "resultado": info_doc})
            return (
                f"Pra fazer a simulação é bem simples{nome_tratamento}: RG e CPF (ou CNH), comprovante de residência, estado civil e comprovante de renda (e extrato do FGTS, se tiver).\n"
                "Por segurança, você leva os documentos direto pro vendedor na visita, sem precisar mandar foto por aqui, tá?\n"
                "Fica melhor pra você ir conhecer e simular na terça às 15h ou na quarta às 10h?",
                tools_chamadas,
            )

        if any(k in msg_norm for k in ("onde fica o plantao", "onde fica o stand", "qual o horario de atendimento", "endereco da construtora")):
            info_pl = self.institucional.consultar_topico("plantao", cidade=lead.cidade)
            tools_chamadas.append({"tool": "consultar_informacoes_institucionais", "resultado": info_pl})
            return (
                f"Nosso atendimento humano e plantões funcionam de {info_pl['horario_atendimento_humano']}{nome_tratamento} 😊\n"
                "Temos plantão no Centro de Tubarão, no Centro de Capivari de Baixo e visitas agendadas em Pescaria Brava.\n"
                "Qual dessas cidades fica melhor pra você visitar?",
                tools_chamadas,
            )

        # C. Gatilhos Imediatos de Transbordo (Handover - Seção 10 / 13)
        gatilho_handover: Optional[str] = None
        if any(k in msg_norm for k in ("falar com uma pessoa", "falar com vendedor", "falar com corretor", "atendente humano")):
            gatilho_handover = "Cliente pediu para falar diretamente com uma pessoa"
        elif any(k in msg_norm for k in ("desconto", "negociar", "proposta", "permuta", "carro no negocio", "parcelar a entrada")):
            gatilho_handover = f"Pedido de negociação/condição especial: {mensagem.strip()}"
        elif any(k in msg_norm for k in ("qual a taxa", "valor da parcela", "quanto fica a parcela", "juros")):
            gatilho_handover = "Dúvida sobre taxas/valor exato de parcelas para simulação"
        elif lead.renda_bruta_valor_aproximado and lead.renda_bruta_valor_aproximado > 13000:
            gatilho_handover = "Renda acima de R$ 13.000 (avaliação com outros bancos)"
        elif lead.restricao_cpf and lead.restricao_cpf.startswith("Sim"):
            gatilho_handover = f"Relatou pendência no CPF ({lead.restricao_cpf}) - análise com correspondente"
        elif "terreno proprio" in msg_norm or "construir no meu terreno" in msg_norm:
            gatilho_handover = "Interesse em construção em terreno próprio"
        elif any(k in msg_norm for k in ("reclamacao", "insatisfeito", "absurdo", "pessimo")):
            gatilho_handover = "Reclamação/insatisfação - encaminhar ao gestor"

        if gatilho_handover:
            if not lead.imoveis_apresentados:
                res_xml = self.catalogo.buscar_imoveis(
                    cidade=lead.cidade,
                    tipo=lead.tipo_imovel,
                    quartos=lead.quartos,
                    faixa_mcmv=lead.pre_enquadramento_mcmv,
                    renda_bruta=lead.renda_bruta_valor_aproximado,
                )
                codigos = [im["codigo"] for im in res_xml.get("imoveis", [])]
                if codigos:
                    self.crm.atualizar_lead(
                        telefone,
                        imoveis_apresentados=codigos,
                        imovel_maior_interesse=res_xml["imoveis"][0]["nome"],
                    )
                tools_chamadas.append({"tool": "buscar_imoveis", "resultado": res_xml})

            res_trans = self.crm.transferir_para_vendedor(
                telefone=telefone,
                motivo_transferencia=gatilho_handover,
            )
            tools_chamadas.append({"tool": "transferir_para_vendedor", "resultado": res_trans})

            if lead.restricao_cpf and lead.restricao_cpf.startswith("Sim"):
                return (
                    f"Obrigada por me contar{nome_tratamento}! Pra financiar o ideal é regularizar essa pendência, "
                    "mas nosso especialista já analisa isso com o correspondente.\n"
                    "Você já tá vendo como regularizar?\n"
                    f"Prontinho! Passei tudo pro vendedor {res_trans['vendedor_responsavel']}, que vai falar com você {res_trans['prazo_retorno']}. O melhor da construção te espera!",
                    tools_chamadas,
                )

            return (
                f"Perfeito{nome_tratamento}! Esse detalhe de condições e simulação quem monta sob medida pra você é o nosso especialista.\n"
                f"Prontinho! Passei tudo pro {res_trans['vendedor_responsavel']}, que vai falar com você {res_trans['prazo_retorno']}.\n"
                "O melhor da construção te espera!",
                tools_chamadas,
            )

        # D. Contorno de Objeções (Seção 9: Acolha -> Valide -> Pergunte)
        if "esta caro" in msg_norm or "muito caro" in msg_norm or "achei caro" in msg_norm:
            return (
                f"Entendo perfeitamente{nome_tratamento}, faz sentido avaliar com calma.\n"
                "Mas me diz: você achou caro comparado ao aluguel que paga hoje ou a outro imóvel que viu?",
                tools_chamadas,
            )
        if "vou pensar" in msg_norm or "preciso pensar" in msg_norm:
            return (
                f"Claro{nome_tratamento}! É uma decisão importante mesmo 😊\n"
                "Me conta: o que você gostaria de avaliar melhor antes de dar o próximo passo?",
                tools_chamadas,
            )
        if any(k in msg_norm for k in ("conversar com minha esposa", "conversar com meu marido", "falar com minha esposa")):
            return (
                f"Faz todo sentido decidirem juntos{nome_tratamento} 😊\n"
                "Que tal vocês virem juntos conhecer o imóvel? Fica melhor pra vocês na terça às 15h ou na quarta às 10h?",
                tools_chamadas,
            )
        if "nao tenho entrada" in msg_norm or "sem entrada" in msg_norm:
            return (
                f"Entendo perfeitamente{nome_tratamento}! Muita gente começa com essa dúvida.\n"
                "Você tem saldo de FGTS ou alguém da família pra compor a renda? Vamos ver todas as possibilidades.",
                tools_chamadas,
            )
        if "usado e mais barato" in msg_norm or "imovel usado" in msg_norm:
            return (
                f"Faz sentido comparar{nome_tratamento}! Mas você sabia que na Faixa 4 o imóvel novo financia até 80%, "
                "enquanto o usado financia só 60%?\n"
                "Você já comparou quanto de entrada precisaria desembolsar em cada um?",
                tools_chamadas,
            )

        # E. Se pedir preço antes da qualificação básica
        qualificacao_minima_ok = bool(
            lead.nome and lead.cidade and lead.tipo_imovel and lead.renda_bruta_familiar_faixa
        )
        if (
            any(k in msg_norm for k in ("qual o preco", "qual o valor", "quanto custa", "passa os valores"))
            and not qualificacao_minima_ok
        ):
            return (
                f"Antes de te passar os valores certinhos{nome_tratamento}, posso te fazer umas perguntinhas rápidas?\n"
                "Assim eu vejo as condições do Minha Casa, Minha Vida que podem valer pra você.\n"
                + self._proxima_pergunta_qualificacao(lead),
                tools_chamadas,
            )

        # F. Se o cliente respondeu escolhendo dia/horário de visita
        if lead.imoveis_apresentados and any(
            k in msg_norm
            for k in ("terca", "quarta", "quinta", "sexta", "sabado", "manha", "tarde", "10h", "15h", "visitar")
        ):
            res_visita = self.crm.registrar_preferencia_visita(
                telefone=telefone,
                opcoes_dia_periodo=mensagem.strip(),
            )
            tools_chamadas.append({"tool": "registrar_preferencia_visita", "resultado": res_visita})
            res_trans = self.crm.transferir_para_vendedor(
                telefone=telefone,
                motivo_transferencia=f"Cliente escolheu horário para visita: {mensagem.strip()}",
            )
            tools_chamadas.append({"tool": "transferir_para_vendedor", "resultado": res_trans})
            return (
                f"Que ótimo{nome_tratamento}! Já anotei sua preferência de visita como a confirmar 😊\n"
                f"Prontinho! Passei tudo pro vendedor {res_trans['vendedor_responsavel']}, que vai falar com você {res_trans['prazo_retorno']} pra confirmar o horário.\n"
                "O melhor da construção te espera!",
                tools_chamadas,
            )

        # G. Busca e apresentação obrigatória de imóveis na base XML
        if (
            lead.cidade
            and (lead.tipo_imovel or lead.quartos)
            and lead.renda_bruta_familiar_faixa
            and not lead.imoveis_apresentados
        ):
            res_xml = self.catalogo.buscar_imoveis(
                cidade=lead.cidade,
                tipo=lead.tipo_imovel,
                quartos=lead.quartos,
                faixa_mcmv=lead.pre_enquadramento_mcmv,
                renda_bruta=lead.renda_bruta_valor_aproximado,
            )
            tools_chamadas.append({"tool": "buscar_imoveis", "resultado": res_xml})
            imoveis = res_xml.get("imoveis", [])

            if imoveis:
                codigos = [im["codigo"] for im in imoveis]
                self.crm.atualizar_lead(
                    telefone,
                    imoveis_apresentados=codigos,
                    imovel_maior_interesse=imoveis[0]["nome"],
                )
                principal = imoveis[0]
                obs = f" ({principal['observacao_compatibilidade']})" if principal.get("observacao_compatibilidade") else ""
                faixa_txt = lead.pre_enquadramento_mcmv or "Minha Casa, Minha Vida"
                return (
                    f"Pelo que você me contou{nome_tratamento}, você se encaixa, em princípio, na {faixa_txt} (os valores certinhos saem na simulação).\n"
                    f"Uma ótima opção pra sair do aluguel é o {principal['nome']} ({principal['bairro']}, {principal['cidade']}){obs}: {principal['tipologia']}, {principal['metragem_privativa']}, {principal['valor_formatado']}, {principal['status_entrega']}, com {principal['diferencial']} ({principal['link']}).\n"
                    "Pra conhecer de perto e fazer uma simulação sem compromisso, fica melhor pra você terça às 15h ou quarta às 10h?",
                    tools_chamadas,
                )

            return (
                f"Procurei aqui na nossa base{nome_tratamento} e hoje não temos uma unidade disponível exatamente com esse filtro dentro do teto da cidade.\n"
                "Já deixei sua demanda registrada pra te avisar assim que abrir uma oportunidade!\n"
                "Quer que eu veja opções em uma cidade vizinha como Tubarão ou Capivari de Baixo?",
                tools_chamadas,
            )

        # H. Condução natural das perguntas de qualificação faltantes
        return (self._proxima_pergunta_qualificacao(lead), tools_chamadas)

    def _proxima_pergunta_qualificacao(self, lead: RegistroLeadCRM) -> str:
        """Retorna a próxima mensagem de qualificação (máx 3 linhas, máx 2 perguntas)."""
        nome_trat = f", {lead.nome}" if lead.nome else ""

        if not lead.nome:
            return (
                "Oi! Aqui é a Lili, assistente virtual da Construtora Demo 😊\n"
                "Com quem eu falo?\n"
                "Me conta: você tá procurando seu primeiro imóvel pra morar ou pra investir?"
            )

        if not lead.cidade or not lead.tipo_imovel:
            return (
                f"Prazer em falar com você{nome_trat}! Que passo bacana 😊\n"
                "Em qual cidade você quer morar (Tubarão, Capivari de Baixo ou Pescaria Brava)?\n"
                "E você prefere casa ou apartamento, de quantos quartos?"
            )

        if not lead.quartos:
            return (
                f"Bacana{nome_trat}! Temos projetos ótimos nessa região 😊\n"
                "Quantos quartos você precisa pra ficar confortável?\n"
                "E é o seu primeiro imóvel ou alguém que vai comprar já tem financiamento ativo?"
            )

        if not lead.renda_bruta_familiar_faixa:
            return (
                f"Perfeito{nome_trat}! Agora, pra eu ver as condições do programa que valem pra você:\n"
                "Somando todo mundo que vai compor a renda, quanto dá por mês antes dos descontos (até R$ 5 mil, de R$ 5 mil a R$ 9.600 ou acima)?\n"
                "Essa renda é de carteira assinada, autônomo ou um pouco de cada?"
            )

        if not lead.entrada_disponivel and not lead.fgts_mais_3_anos:
            return (
                f"Ótimo{nome_trat}! Com essa faixa você já conta com condições excelentes no Minha Casa, Minha Vida.\n"
                "Você tem FGTS (com pelo menos 3 anos de carteira assinada no total) ou algum valor separado pra entrada?\n"
                "E quem vai morar com você no imóvel?"
            )

        if not lead.prazo_compra or not lead.restricao_cpf:
            return (
                f"Show{nome_trat}! Já estou separando os imóveis compatíveis pra você.\n"
                "Pra quando você pensa em se mudar?\n"
                "E pra eu já te orientar certinho: tem alguma pendência no CPF hoje?"
            )

        return (
            f"Pra conhecer o imóvel e fazer uma simulação sem compromisso{nome_trat}, "
            "fica melhor pra você terça às 15h ou quarta às 10h?"
        )
