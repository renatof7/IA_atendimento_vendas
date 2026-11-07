"""
Motor de Classificação de Lead (Pontuação, Temperatura e SLA de Retorno).
Calculado por regras determinísticas (Seção 11 das Instruções Mestras),
nunca por impressão subjetiva da IA.
"""

from datetime import datetime
from typing import Optional
from app.config import settings


CRITERIOS_ELIMINATORIOS = {
    "locacao": "Busca apenas locação (a construtora não opera locação)",
    "cidade_sem_produto": "Busca exclusivamente cidade onde a construtora não possui estoque",
    "corretor_parceiro": "Corretor de outra imobiliária buscando parceria (encaminhar ao responsável)",
    "imprensa_fornecedor_curriculo": "Imprensa, fornecedor ou envio de currículo (informar canal correto)",
    "spam": "Linguagem ofensiva persistente, spam ou contato errado",
}


def calcular_pontuacao_e_temperatura(
    prazo_compra: Optional[str] = None,
    pre_enquadrado_com_estoque: bool = False,
    viabilidade_entrada_fgts_composicao: bool = False,
    aceitou_visita_ou_pediu_vendedor: bool = False,
    respondeu_todas_obrigatorias: bool = False,
    imovel_ou_financiamento_ativo: bool = False,
    criterio_eliminatorio: Optional[str] = None,
    horario_atual: Optional[datetime] = None,
) -> dict:
    """
    Calcula a pontuação, temperatura (Quente, Morno, Frio, Sem perfil)
    e o prazo máximo (SLA) para o vendedor assumir o atendimento.
    """
    if criterio_eliminatorio:
        descricao_motivo = CRITERIOS_ELIMINATORIOS.get(
            criterio_eliminatorio, criterio_eliminatorio
        )
        return {
            "pontuacao": 0,
            "temperatura": "Sem perfil",
            "detalhamento_pontos": {"criterio_eliminatorio": descricao_motivo},
            "acao": "Encerramento cordial, com motivo registrado no CRM.",
            "prazo_retorno_vendedor": "Não aplicável (sem passagem comercial)",
        }

    pontos = 0
    detalhamento: dict[str, int] = {}

    # 1. Prazo de compra: até 3 meses (+30) | de 3 a 12 meses (+15)
    if prazo_compra:
        p_norm = prazo_compra.strip().lower()
        if any(
            termo in p_norm
            for termo in ["ate 3", "até 3", "imediato", "1 mes", "2 meses", "3 meses", "fevereiro", "já", "agora"]
        ):
            pontos += 30
            detalhamento["prazo_ate_3_meses"] = 30
        elif any(
            termo in p_norm
            for termo in ["3 a 6", "6 a 12", "3 a 12", "este ano", "esse ano", "6 meses", "1 ano"]
        ):
            pontos += 15
            detalhamento["prazo_3_a_12_meses"] = 15

    # 2. Pré-enquadrado em uma faixa MCMV, com imóvel compatível no estoque (+25)
    if pre_enquadrado_com_estoque:
        pontos += 25
        detalhamento["pre_enquadrado_mcmv_com_estoque"] = 25

    # 3. Entrada, FGTS ou composição de renda que viabiliza a compra (+20)
    if viabilidade_entrada_fgts_composicao:
        pontos += 20
        detalhamento["entrada_fgts_ou_composicao_viavel"] = 20

    # 4. Aceitou visita ou pediu contato do vendedor (+20)
    if aceitou_visita_ou_pediu_vendedor:
        pontos += 20
        detalhamento["aceitou_visita_ou_pediu_vendedor"] = 20

    # 5. Respondeu todas as perguntas obrigatórias (+5)
    if respondeu_todas_obrigatorias:
        pontos += 5
        detalhamento["respondeu_todas_obrigatorias"] = 5

    # 6. Imóvel ou financiamento habitacional ativo (-40)
    if imovel_ou_financiamento_ativo:
        pontos -= 40
        detalhamento["imovel_ou_financiamento_ativo"] = -40

    agora = horario_atual or datetime.now()
    em_horario_comercial = (
        settings.HORARIO_COMERCIAL_INICIO <= agora.hour < settings.HORARIO_COMERCIAL_FIM
        and agora.weekday() < 6
    )

    if pontos >= 70:
        temperatura = "Quente"
        acao = "Passagem imediata ao vendedor, com notificação prioritária"
        prazo_vendedor = (
            "em até 30 minutos"
            if em_horario_comercial
            else "até as 10h de amanhã"
        )
    elif pontos >= 40:
        temperatura = "Morno"
        acao = "Passagem ao vendedor, com retorno no mesmo dia"
        prazo_vendedor = (
            "em até 4 horas"
            if em_horario_comercial
            else "no próximo período comercial (em até 4 horas após abertura)"
        )
    else:
        temperatura = "Frio"
        acao = "Nutrição automática; o vendedor vê no CRM, sem urgência"
        prazo_vendedor = "em até 48 horas"

    return {
        "pontuacao": pontos,
        "temperatura": temperatura,
        "detalhamento_pontos": detalhamento,
        "acao": acao,
        "prazo_retorno_vendedor": prazo_vendedor,
    }
