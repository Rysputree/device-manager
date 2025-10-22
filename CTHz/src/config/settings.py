from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    environment: str = "development"  # development|production
    secret_key: str = "dev-secret-key-change-me"
    access_token_exp_hours: int = 8
    refresh_token_exp_days: int = 7

    database_url: str = "sqlite:///./data/cthz.db"

    # Audit sink configuration: db | file | both
    audit_sink_mode: str = "db"
    audit_log_file: str = "./logs/audit.log"
    audit_backup_count: int = 7

    class Config:
        env_prefix = "CTHZ_"
        env_file = ".env" 