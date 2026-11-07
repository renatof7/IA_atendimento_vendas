"""Configurações centrais do projeto Lili IA (Motor de Pré-Vendas Imobiliárias)."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass


class Settings:
    """Configurações carregadas do ambiente ou padrões."""

    PROJECT_NAME: str = "Lili IA — Assistente de Pré-Vendas MCMV (GroqCloud + Evolution API)"
    VERSION: str = "2.0.0"

    # Provedores Ativos
    IA_PROVIDER: str = os.getenv("IA_PROVIDER", "groq")  # 'groq', 'claude', 'local'
    WHATSAPP_PROVIDER: str = os.getenv("WHATSAPP_PROVIDER", "evolution")  # 'evolution', 'meta'

    # GroqCloud (Motor Principal de IA)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
    GROQ_MAX_TOKENS: int = int(os.getenv("GROQ_MAX_TOKENS", "600"))
    GROQ_TEMPERATURE: float = float(os.getenv("GROQ_TEMPERATURE", "0.2"))
    GROQ_BASE_URL: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

    # Anthropic Claude (Opção Secundária / Fallback)
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    ANTHROPIC_MAX_TOKENS: int = int(os.getenv("ANTHROPIC_MAX_TOKENS", "600"))

    # Evolution API (WhatsApp Gateway QR Code)
    EVOLUTION_API_URL: str = os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
    EVOLUTION_API_KEY: str = os.getenv("EVOLUTION_API_KEY", "imob_evolution_secret_2026")
    EVOLUTION_INSTANCE_NAME: str = os.getenv("EVOLUTION_INSTANCE_NAME", "lili-whatsapp")

    # Base XML de Imóveis
    XML_IMOVEIS_PATH: Path = BASE_DIR / os.getenv("XML_IMOVEIS_PATH", "data/imoveis.xml")
    XML_REFRESH_INTERVAL_SECONDS: int = int(os.getenv("XML_REFRESH_INTERVAL_SECONDS", "3600"))

    # CRM Agendor (API v3)
    AGENDOR_API_TOKEN: str = os.getenv("AGENDOR_API_TOKEN", "")
    AGENDOR_API_URL: str = os.getenv("AGENDOR_API_URL", "https://api.agendor.com.br/v3")
    AGENDOR_FUNIL_ID: int = int(os.getenv("AGENDOR_FUNIL_ID", "1"))
    CRM_STORAGE_PATH: Path = BASE_DIR / os.getenv("CRM_STORAGE_PATH", "data/crm_agendor_leads.json")

    # WhatsApp Business Cloud API (Meta Oficial - Opcional)
    WHATSAPP_ACCESS_TOKEN: str = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    WHATSAPP_VERIFY_TOKEN: str = os.getenv("WHATSAPP_VERIFY_TOKEN", "imob_lili_verify_2026")
    WHATSAPP_GRAPH_API_VERSION: str = os.getenv("WHATSAPP_GRAPH_API_VERSION", "v21.0")

    # Operação Comercial e Plantão
    VENDEDOR_PADRAO_NOME: str = os.getenv("VENDEDOR_PADRAO_NOME", "Carlos Eduardo")
    HORARIO_COMERCIAL_INICIO: int = int(os.getenv("HORARIO_COMERCIAL_INICIO", "8"))
    HORARIO_COMERCIAL_FIM: int = int(os.getenv("HORARIO_COMERCIAL_FIM", "18"))
    HORARIOS_PLANTAO: str = os.getenv(
        "HORARIOS_PLANTAO",
        "Segunda a Sexta das 8h30 às 18h30 e Sábados das 9h às 13h",
    )
    CIDADES_ATENDIDAS: list[str] = ["Capivari de Baixo", "Tubarão", "Pescaria Brava"]


settings = Settings()
