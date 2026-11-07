"""
Definição de Tools (Function Calling) no formato nativo da API GroqCloud / OpenAI (Llama 3.3 70B).
Mapeia as 7 ferramentas de atendimento da Lili IA:
1. buscar_imoveis
2. detalhar_imovel
3. atualizar_lead
4. calcular_pre_enquadramento_mcmv
5. registrar_preferencia_visita
6. transferir_para_vendedor
7. encerrar_sem_perfil
8. consultar_informacoes_institucionais
"""

from app.agent.claude_tools import CLAUDE_TOOLS_SCHEMA

# Converte o esquema Claude (input_schema) para o formato padrão OpenAI / Groq (type: function, parameters)
GROQ_TOOLS_SCHEMA: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": tool["input_schema"],
        },
    }
    for tool in CLAUDE_TOOLS_SCHEMA
]
