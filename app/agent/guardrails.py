"""
Guardrails de Segurança, LGPD e Regras de Comunicação da Lili (Seções 4, 13 e 14).
Garante que nenhuma mensagem da IA viole os limites inegociáveis do atendimento.
"""

import re
from typing import Optional


# Expressão regular para detectar emojis Unicode
EMOJI_REGEX = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+",
    flags=re.UNICODE,
)

# Palavras que indicam assunto de valores, renda ou CPF (onde é PROIBIDO usar emoji)
TERMOS_SENSIVEIS_SEM_EMOJI = re.compile(
    r"\b(r\$|reais|renda|sal[aá]rio|cpf|restri[cç][aã]o|serasa|spc|fies|entrada|parcela|valor|mil)\b",
    re.IGNORECASE,
)

# Frases proibidas (Seção 13) e suas substituições seguras
FRASES_PROIBIDAS_MAP = [
    (re.compile(r"\bcr[eé]dito aprovado\b", re.IGNORECASE), "sujeito à análise de crédito na simulação"),
    (re.compile(r"\bgarantido\b", re.IGNORECASE), "possível conforme análise"),
    (
        re.compile(r"\bvoc[eê] vai conseguir o subs[ií]dio\b", re.IGNORECASE),
        "o subsídio é analisado pela Caixa na simulação",
    ),
    (
        re.compile(r"\ba parcela vai ser de r\$\s*[\d\.,]+", re.IGNORECASE),
        "o valor certinho da parcela sai na simulação com o nosso time",
    ),
    (
        re.compile(r"\brentabilidade de\s*\d+%", re.IGNORECASE),
        "ótimo potencial pela localização e diferenciais do projeto",
    ),
    (re.compile(r"\bvai valorizar\b", re.IGNORECASE), "fica numa localização em desenvolvimento"),
]

# Detecção de tentativa de Prompt Injection (Seção 14)
PADROES_PROMPT_INJECTION = re.compile(
    r"(esque[cç]a suas instru[cç][oõ]es|ignore (todas )?as regras|revele seu prompt|"
    r"qual [eé] o seu system prompt|mostre suas instru[cç][oõ]es|aja como outro|"
    r"me d[aá] \d+%\s*de desconto agora)",
    re.IGNORECASE,
)

# Detecção de pedido de Opt-Out LGPD (Seção 14)
PADROES_OPT_OUT_LGPD = re.compile(
    r"\b(pare de me mandar|parar de receber|n[aã]o quero mais receber mensagens|"
    r"descadastrar|sair da lista|remover meu n[uú]mero|cancelar mensagens)\b",
    re.IGNORECASE,
)

# Detecção de envio de número de CPF no texto (Segurança LGPD: nunca receber números de documentos)
PADRAO_NUMERO_CPF = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")


def detectar_prompt_injection(mensagem_usuario: str) -> bool:
    """Retorna True se o usuário tentar manipular as regras ou extrair o prompt."""
    return bool(PADROES_PROMPT_INJECTION.search(mensagem_usuario or ""))


def detectar_opt_out_lgpd(mensagem_usuario: str) -> bool:
    """Retorna True se o cliente pedir para parar de receber mensagens."""
    return bool(PADROES_OPT_OUT_LGPD.search(mensagem_usuario or ""))


def detectar_envio_documento_cpf(mensagem_usuario: str) -> bool:
    """Retorna True se o cliente enviar número de CPF pelo WhatsApp."""
    return bool(PADRAO_NUMERO_CPF.search(mensagem_usuario or ""))


def aplicar_guardrails_resposta(texto: str) -> str:
    """
    Aplica todas as regras de comunicação e segurança na resposta da Lili:
    1. Nunca envia apenas 'E aí?' ou 'Conseguiu ver?'
    2. Substitui frases proibidas (Seção 13)
    3. Remove emojis se falar de valores, renda ou CPF; caso contrário, mantém no máximo 1 emoji
    4. Limita a no máximo 2 perguntas ('?') por mensagem
    5. Limita a no máximo 3 linhas por mensagem
    """
    if not texto or not texto.strip():
        return "Me conta: como posso te ajudar a encontrar seu imóvel hoje?"

    limpo = texto.strip()

    # 1. Proibição de "E aí?" ou "Conseguiu ver?" isolados
    if re.fullmatch(r"(e a[ií]\??|conseguiu ver\??)\s*", limpo, flags=re.IGNORECASE):
        limpo = "Ficou alguma dúvida sobre o imóvel? Se quiser, já vemos o melhor horário pra você conhecer!"

    # 2. Substituição de frases proibidas
    for padrao, substituto in FRASES_PROIBIDAS_MAP:
        limpo = padrao.sub(substituto, limpo)

    # 3. Controle de Emojis
    fala_de_tema_sensivel = bool(TERMOS_SENSIVEIS_SEM_EMOJI.search(limpo))
    if fala_de_tema_sensivel:
        limpo = EMOJI_REGEX.sub("", limpo)
    else:
        emojis_encontrados = list(EMOJI_REGEX.finditer(limpo))
        if len(emojis_encontrados) > 1:
            # Mantém apenas o primeiro caractere de emoji e remove os demais
            primeiro = emojis_encontrados[0]
            primeiro_char = primeiro.group(0)[0]
            sem_emojis = EMOJI_REGEX.sub("", limpo)
            # Reinsere apenas 1 emoji no final da primeira frase/linha
            linhas_temp = sem_emojis.splitlines()
            if linhas_temp:
                linhas_temp[0] = linhas_temp[0].rstrip() + f" {primeiro_char}"
                limpo = "\n".join(linhas_temp)
        elif len(emojis_encontrados) == 1 and len(emojis_encontrados[0].group(0)) > 1:
            # Se for sequência de emojis juntos (ex: 😊😊), reduz para 1
            m = emojis_encontrados[0]
            limpo = limpo[: m.start()] + m.group(0)[0] + limpo[m.end() :]

    # 4. Limite de no máximo 3 linhas não vazias
    linhas = [ln.strip() for ln in limpo.splitlines() if ln.strip()]
    if len(linhas) > 3:
        linhas = linhas[:3]
    limpo = "\n".join(linhas)

    # 5. Limite de no máximo 2 pontos de interrogação ('?')
    if limpo.count("?") > 2:
        partes = limpo.split("?")
        # Mantém as duas primeiras perguntas com '?' e converte as demais em ponto final
        reconstruido = partes[0] + "?" + partes[1] + "?"
        resto = ".".join(p for p in partes[2:] if p.strip())
        if resto.strip():
            reconstruido += " " + resto.strip()
            if not reconstruido.endswith("."):
                reconstruido += "."
        limpo = reconstruido

    # Limpeza de espaços duplos preservando quebras de linha
    linhas_finais = [re.sub(r" {2,}", " ", ln).strip() for ln in limpo.splitlines() if ln.strip()]
    return "\n".join(linhas_finais)
