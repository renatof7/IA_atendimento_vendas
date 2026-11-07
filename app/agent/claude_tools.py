"""
Definição de Tools (Function Calling) no formato nativo da API Anthropic Claude (`input_schema`).
Cobre as ferramentas obrigatórias da especificação + cálculo MCMV 2026.
"""

CLAUDE_TOOLS_SCHEMA: list[dict] = [
    {
        "name": "buscar_imoveis",
        "description": (
            "Consulta obrigatoriamente a base XML vigente da construtora com filtros e devolve "
            "as opções disponíveis dentro do teto da cidade no Minha Casa, Minha Vida 2026. "
            "Nunca cite empreendimentos, valores, metragens ou disponibilidades sem usar esta ferramenta."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cidade": {
                    "type": "string",
                    "description": "Cidade desejada (ex: 'Tubarão', 'Capivari de Baixo', 'Pescaria Brava' ou 'Qualquer').",
                },
                "bairro": {
                    "type": "string",
                    "description": "Bairro de preferência, se informado.",
                },
                "tipo": {
                    "type": "string",
                    "description": "Tipo do imóvel ('Apartamento' ou 'Casa').",
                },
                "quartos": {
                    "type": "integer",
                    "description": "Quantidade de quartos desejada (ex: 2, 3).",
                },
                "valor_maximo": {
                    "type": "number",
                    "description": "Valor máximo de busca em reais, se aplicável.",
                },
                "faixa_mcmv": {
                    "type": "string",
                    "description": "Faixa do MCMV 2026 ('Faixa 1', 'Faixa 2', 'Faixa 3', 'Faixa 4').",
                },
                "status_entrega": {
                    "type": "string",
                    "description": "Status da obra ('Lançamento', 'Em obra', 'Pronto para morar').",
                },
            },
            "required": [],
        },
    },
    {
        "name": "detalhar_imovel",
        "description": "Traz a ficha completa, fotos, diferenciais, metragem privativa e link de um empreendimento pelo código XML.",
        "input_schema": {
            "type": "object",
            "properties": {
                "codigo": {
                    "type": "string",
                    "description": "Código do imóvel na base XML (ex: 'IMOB-TUB-001').",
                }
            },
            "required": ["codigo"],
        },
    },
    {
        "name": "atualizar_lead",
        "description": (
            "Grava imediatamente no CRM Agendor cada informação de qualificação assim que coletada "
            "(nome, objetivo, primeiro_imovel, cidade, tipo_imovel, quartos, renda_bruta_familiar_faixa, "
            "tipo_renda, fgts_mais_3_anos, dependentes, imovel_ou_financiamento_ativo, restricao_cpf, "
            "entrada_disponivel, prazo_compra)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "nome": {"type": "string", "description": "Nome do cliente."},
                "objetivo": {"type": "string", "description": "'morar', 'investir' ou 'outro'."},
                "primeiro_imovel": {"type": "string", "description": "'Sim' ou 'Não'."},
                "cidade": {"type": "string", "description": "Cidade de interesse."},
                "tipo_imovel": {"type": "string", "description": "'Apartamento' ou 'Casa'."},
                "quartos": {"type": "integer", "description": "Quantidade de quartos."},
                "renda_bruta_familiar_faixa": {
                    "type": "string",
                    "description": "Faixa de renda familiar bruta mensal informada pelo cliente.",
                },
                "renda_bruta_valor_aproximado": {
                    "type": "number",
                    "description": "Valor numérico aproximado da renda bruta familiar mensal em R$.",
                },
                "tipo_renda": {
                    "type": "string",
                    "description": "'Formal (CLT)', 'Autônomo / PJ' ou 'Mista'.",
                },
                "fgts_mais_3_anos": {
                    "type": "string",
                    "description": "'Sim', 'Não' ou 'Prefiro não informar'.",
                },
                "dependentes": {"type": "string", "description": "Quem vai morar com o cliente."},
                "imovel_ou_financiamento_ativo": {
                    "type": "string",
                    "description": "'Sim' ou 'Não'.",
                },
                "restricao_cpf": {
                    "type": "string",
                    "description": "'Sim', 'Não' ou 'Não informado'.",
                },
                "entrada_disponivel": {
                    "type": "string",
                    "description": "Faixa ou valor de entrada disponível.",
                },
                "prazo_compra": {
                    "type": "string",
                    "description": "'até 3 meses', '3 a 6 meses', '6 a 12 meses' ou 'mais de 12 meses'.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "calcular_pre_enquadramento_mcmv",
        "description": (
            "Executa o cálculo interno da Tabela MCMV 2026 (Faixas 1 a 4, tetos de Capivari de Baixo, "
            "Tubarão e Pescaria Brava, cota 80% novo vs 60% usado). Use apenas para escolher imóveis e pontuar o lead."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "renda_bruta": {"type": "number", "description": "Renda familiar bruta mensal em R$."},
                "faixa_informada": {"type": "string", "description": "Faixa informada (ex: 'Faixa 2', 'Faixa 3')."},
                "cidade": {"type": "string", "description": "Cidade para verificar o teto do MCMV."},
                "valor_imovel": {"type": "number", "description": "Valor do imóvel para estimar cota interna."},
                "imovel_novo": {"type": "boolean", "description": "True para imóvel novo (80%), False para usado (60% na Faixa 4)."},
            },
            "required": [],
        },
    },
    {
        "name": "registrar_preferencia_visita",
        "description": (
            "Registra no CRM Agendor 2 ou 3 opções de dia e período (manhã, tarde, noite) e local "
            "sempre com status 'visita a confirmar'. A IA nunca confirma o horário sozinha."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "opcoes_dia_periodo": {
                    "type": "string",
                    "description": "Opções de dia e horário preferidas pelo cliente (ex: 'terça às 15h ou quarta às 10h').",
                },
                "local": {
                    "type": "string",
                    "description": "Local da visita ('Stand', 'Decorado', 'Obra' ou 'Imóvel pronto').",
                },
            },
            "required": ["opcoes_dia_periodo"],
        },
    },
    {
        "name": "transferir_para_vendedor",
        "description": (
            "Grava o resumo de até 6 linhas no CRM Agendor, calcula a temperatura e SLA do vendedor "
            "e transfere o atendimento. Use quando o cliente pedir pessoa humana, quiser negociar, "
            "perguntar parcelas/taxas, tiver renda > R$ 13.000, relatar restrição no CPF, reclamar ou agendar visita."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "motivo_transferencia": {
                    "type": "string",
                    "description": "Motivo claro do transbordo para o vendedor.",
                },
                "duvidas_ou_objecoes": {
                    "type": "string",
                    "description": "Dúvidas ou objeções em aberto para o vendedor tratar.",
                },
            },
            "required": ["motivo_transferencia"],
        },
    },
    {
        "name": "encerrar_sem_perfil",
        "description": (
            "Registra o motivo eliminatório no CRM Agendor ('locacao', 'cidade_sem_produto', "
            "'corretor_parceiro', 'imprensa_fornecedor_curriculo', 'spam') e encerra com cordialidade."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "motivo": {
                    "type": "string",
                    "description": "Critério eliminatório identificado.",
                }
            },
            "required": ["motivo"],
        },
    },
    {
        "name": "consultar_informacoes_institucionais",
        "description": (
            "Consulta a base institucional oficial da construtora: endereços e horários dos plantões/stands, "
            "horário de atendimento humano, lista de documentação básica para simulação, diferenciais "
            "construtivos, canais de pós-venda/assistência/boleto, parcerias com corretores, RH/fornecedores e FAQ."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topico": {
                    "type": "string",
                    "description": "Tópico desejado ('plantao', 'documentacao', 'pos_venda', 'parcerias', 'fornecedor', 'diferenciais', 'faq').",
                },
                "cidade": {
                    "type": "string",
                    "description": "Cidade opcional para filtrar o endereço do stand ('Tubarão', 'Capivari de Baixo', 'Pescaria Brava').",
                },
            },
            "required": ["topico"],
        },
    },
]
