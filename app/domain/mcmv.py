"""
Motor de Pré-Enquadramento Minha Casa, Minha Vida (MCMV) 2026.
Fonte oficial: Guia Rápido do Vendedor MCMV 2026 (Tabela Referencial).
Sempre utiliza a RENDA FAMILIAR BRUTA (nunca a líquida).
"""

from dataclasses import dataclass
from typing import Optional
import unicodedata


def _normalizar_texto(texto: str) -> str:
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFKD", texto.strip().lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


@dataclass(frozen=True)
class RegraFaixaMCMV:
    faixa: str
    renda_min: float
    renda_max: float
    teto_capivari_de_baixo: float
    teto_tubarao: float
    teto_pescaria_brava: float
    teto_demais_cidades: float
    cota_novo: float
    cota_usado: float
    financia_ate_novo: float
    financia_ate_usado: float
    juros_ref_interna: str


TABELA_MCMV_2026: list[RegraFaixaMCMV] = [
    RegraFaixaMCMV(
        faixa="Faixa 1",
        renda_min=1900.00,
        renda_max=2850.00,
        teto_capivari_de_baixo=220_000.00,
        teto_tubarao=235_000.00,
        teto_pescaria_brava=210_000.00,
        teto_demais_cidades=220_000.00,
        cota_novo=0.80,
        cota_usado=0.80,
        financia_ate_novo=176_000.00,
        financia_ate_usado=176_000.00,
        juros_ref_interna="4,00% a.a.",
    ),
    RegraFaixaMCMV(
        faixa="Faixa 2",
        renda_min=2850.01,
        renda_max=5000.00,
        teto_capivari_de_baixo=220_000.00,
        teto_tubarao=235_000.00,
        teto_pescaria_brava=210_000.00,
        teto_demais_cidades=220_000.00,
        cota_novo=0.80,
        cota_usado=0.80,
        financia_ate_novo=176_000.00,
        financia_ate_usado=176_000.00,
        juros_ref_interna="4,75% a 6,50% a.a.",
    ),
    RegraFaixaMCMV(
        faixa="Faixa 3",
        renda_min=5000.01,
        renda_max=9600.00,
        teto_capivari_de_baixo=400_000.00,
        teto_tubarao=400_000.00,
        teto_pescaria_brava=400_000.00,
        teto_demais_cidades=400_000.00,
        cota_novo=0.80,
        cota_usado=0.80,
        financia_ate_novo=320_000.00,
        financia_ate_usado=320_000.00,
        juros_ref_interna="7,66% a.a.",
    ),
    RegraFaixaMCMV(
        faixa="Faixa 4",
        renda_min=9600.01,
        renda_max=13000.00,
        teto_capivari_de_baixo=600_000.00,
        teto_tubarao=600_000.00,
        teto_pescaria_brava=600_000.00,
        teto_demais_cidades=600_000.00,
        cota_novo=0.80,
        cota_usado=0.60,
        financia_ate_novo=480_000.00,
        financia_ate_usado=360_000.00,
        juros_ref_interna="10,00% a.a.",
    ),
]


def obter_regra_por_faixa_ou_renda(
    renda_bruta: Optional[float] = None,
    faixa_informada: Optional[str] = None,
) -> Optional[RegraFaixaMCMV]:
    """
    Localiza a regra MCMV 2026 pela renda bruta familiar ou pelo nome da faixa.
    Retorna None caso a renda esteja acima de R$ 13.000 (fora do programa MCMV).
    """
    if faixa_informada:
        norm = _normalizar_texto(faixa_informada)
        if "faixa 1" in norm or "ate 2850" in norm or "a partir de 1900" in norm:
            return TABELA_MCMV_2026[0]
        if "faixa 2" in norm or "ate 5000" in norm or "ate 5 mil" in norm or "ate r$ 5" in norm:
            return TABELA_MCMV_2026[1]
        if (
            "faixa 3" in norm
            or "segunda faixa" in norm
            or "5000 a 9600" in norm
            or "5 mil a 9" in norm
        ):
            return TABELA_MCMV_2026[2]
        if "faixa 4" in norm or "9600 a 13000" in norm or "9.600 a 13" in norm:
            return TABELA_MCMV_2026[3]

    if renda_bruta is not None:
        if renda_bruta <= 0:
            return None
        if renda_bruta <= 2850.00:
            return TABELA_MCMV_2026[0]
        if renda_bruta <= 5000.00:
            return TABELA_MCMV_2026[1]
        if renda_bruta <= 9600.00:
            return TABELA_MCMV_2026[2]
        if renda_bruta <= 13000.00:
            return TABELA_MCMV_2026[3]
        return None

    return None


def obter_teto_cidade(regra: RegraFaixaMCMV, cidade: Optional[str]) -> float:
    """Retorna o teto do imóvel na cidade informada para a respectiva faixa MCMV."""
    norm = _normalizar_texto(cidade or "")
    if "tubarao" in norm:
        return regra.teto_tubarao
    if "capivari" in norm:
        return regra.teto_capivari_de_baixo
    if "pescaria" in norm or "brava" in norm:
        return regra.teto_pescaria_brava
    # Se cidade estiver em aberto ("qualquer"), usa o maior teto aplicável da faixa (Tubarão)
    if norm in ("", "qualquer", "aberto", "todas"):
        return max(
            regra.teto_tubarao,
            regra.teto_capivari_de_baixo,
            regra.teto_pescaria_brava,
        )
    return regra.teto_demais_cidades


def calcular_pre_enquadramento(
    renda_bruta: Optional[float] = None,
    faixa_informada: Optional[str] = None,
    cidade: Optional[str] = None,
    valor_imovel: Optional[float] = None,
    imovel_novo: bool = True,
) -> dict:
    """
    Executa os 3 passos internos da tabela MCMV 2026:
    1. Renda -> Faixa
    2. Cidade -> Teto
    3. Tipo -> Quanto financia (menor entre valor_imovel * cota e financia_ate)

    IMPORTANTE: Os números de financiamento estimado, entrada estimada e juros são
    ESTRITAMENTE INTERNOS para a Lili escolher imóveis e pontuar o lead.
    """
    if renda_bruta is not None and renda_bruta > 13000.00:
        return {
            "enquadrado_mcmv": False,
            "faixa": "Fora do programa (Renda > R$ 13.000)",
            "motivo": "Renda familiar bruta acima de R$ 13.000,00.",
            "acao_recomendada": (
                "Não descartar: registrar no CRM e transferir ao vendedor, "
                "que avalia outros bancos e linhas de financiamento (SBPE)."
            ),
            "mensagem_permitida_ao_cliente": (
                "Com essa faixa de renda, nosso especialista consegue avaliar linhas "
                "especiais de financiamento pra você na simulação."
            ),
        }

    regra = obter_regra_por_faixa_ou_renda(renda_bruta=renda_bruta, faixa_informada=faixa_informada)
    if not regra:
        return {
            "enquadrado_mcmv": False,
            "faixa": "A definir",
            "motivo": "Renda ou faixa ainda não informada.",
            "acao_recomendada": "Perguntar a faixa de renda bruta familiar somando quem vai compor.",
            "mensagem_permitida_ao_cliente": None,
        }

    teto_cidade = obter_teto_cidade(regra, cidade)
    cota = regra.cota_novo if imovel_novo else regra.cota_usado
    limite_financiamento = regra.financia_ate_novo if imovel_novo else regra.financia_ate_usado

    resultado = {
        "enquadrado_mcmv": True,
        "faixa": regra.faixa,
        "cidade_referencia": cidade or "Todas as cidades atendidas",
        "teto_cidade": teto_cidade,
        "uso_interno_exclusivo": {
            "cota_aplicada": cota,
            "financia_ate_teto_faixa": limite_financiamento,
            "juros_referencia_interna": regra.juros_ref_interna,
            "aviso_seguranca": (
                "PROIBIDO informar ao cliente valor financiado, entrada exata, "
                "taxa de juros, valor de parcela ou subsídio."
            ),
        },
        "mensagem_permitida_ao_cliente": (
            f"Pelo que você me contou, você se encaixa, em princípio, na {regra.faixa} "
            "do Minha Casa, Minha Vida. Os valores certinhos saem na simulação com o nosso time."
        ),
    }

    if valor_imovel is not None:
        dentro_do_teto = valor_imovel <= teto_cidade
        financiamento_estimado = (
            min(valor_imovel * cota, limite_financiamento) if dentro_do_teto else 0.0
        )
        entrada_estimada = (valor_imovel - financiamento_estimado) if dentro_do_teto else valor_imovel
        resultado["analise_imovel_interna"] = {
            "valor_imovel": valor_imovel,
            "dentro_do_teto_cidade": dentro_do_teto,
            "financiamento_estimado_interno": round(financiamento_estimado, 2),
            "entrada_estimada_interna": round(entrada_estimada, 2),
        }

    return resultado
