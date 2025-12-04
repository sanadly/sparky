import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # SAP Configuration
    SAP_CLIENT_ID: str = ""
    SAP_CLIENT_SECRET: str = ""
    SAP_OFFER_GROUP: str = "Simulation Gruppe4"
    
    # SAP URLs
    AUTH_URL: str = "https://intense-ag-development.authentication.eu10.hana.ondemand.com/oauth/token"
    PRODUCT_URL: str = "https://intense-ag-development.it-cpi018-rt.cfapps.eu10-003.hana.ondemand.com/http/v1/s4/upil/product/information"
    SIMULATION_URL: str = "https://intense-ag-development.it-cpi018-rt.cfapps.eu10-003.hana.ondemand.com/http/v1/s4/upil/product/simulation"
    OFFER_URL: str = "https://intense-ag-development.it-cpi018-rt.cfapps.eu10-003.hana.ondemand.com/http/v1/servicecloud/create/offer"
    
    # Gemini Configuration
    GEMINI_API_KEY: str = ""
    GEMINI_API_KEY_2: str = ""
    GEMINI_MODEL: str = "models/gemini-flash-latest"
    
    # DeepSeek Configuration
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    
    # LLM Provider (gemini or deepseek)
    LLM_PROVIDER: str = "deepseek"
    
    # Application Configuration
    LOG_LEVEL: str = "INFO"
    
    # Feature Flags
    MOCK_SAP: bool = False
    MOCK_LLM: bool = False
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""

    # Email Configuration
    SMTP_SERVER: str = ""
    SMTP_PORT: int = 465
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    
    # IMAP Configuration
    IMAP_SERVER: str = ""
    IMAP_PORT: int = 993

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Auto-detect mocks if keys are missing or default
        if not self.SAP_CLIENT_ID or self.SAP_CLIENT_ID == "your_client_id":
            self.MOCK_SAP = True
        if not self.GEMINI_API_KEY or self.GEMINI_API_KEY == "your_gemini_api_key":
            self.MOCK_LLM = True
            
        # Alias for DeepSeek API Key (User request)
        if not self.DEEPSEEK_API_KEY and os.environ.get("DEEPSEEK_API"):
            self.DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API")

settings = Settings()
