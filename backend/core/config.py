"""
Application configuration using Pydantic Settings.
Loads configuration from environment variables and .env file.
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="Mineploy", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")

    # API
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_prefix: str = Field(default="/api/v1", description="API prefix")

    # CORS (stored as string, parsed to list)
    cors_origins: str | list[str] = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        description="Allowed CORS origins (comma-separated)"
    )

    @field_validator("cors_origins", mode="after")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from comma-separated string to list."""
        if isinstance(v, str):
            # If empty string, use defaults
            if not v or v.strip() == "":
                return ["http://localhost:3000", "http://127.0.0.1:3000"]
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # Database (MySQL)
    db_host: str = Field(default="mysql", description="Database host")
    db_port: int = Field(default=3306, description="Database port")
    db_user: str = Field(default="mineploy", description="Database user")
    db_password: str = Field(default="mineploy", description="Database password")
    db_name: str = Field(default="mineploy", description="Database name")
    db_echo: bool = Field(default=False, description="Echo SQL queries")

    @property
    def database_url(self) -> str:
        """Generate MySQL database URL."""
        return (
            f"mysql+aiomysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    # Security
    secret_key: str = Field(
        default="CHANGE_THIS_SECRET_KEY_IN_PRODUCTION",
        description="Secret key for JWT tokens (use openssl rand -hex 32)"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_hours: int = Field(
        default=168,  # 7 days
        description="JWT token expiration in hours"
    )
    refresh_token_expiration_days: int = Field(
        default=30,  # 30 days
        description="Refresh token expiration in days"
    )

    # Docker
    docker_socket: str = Field(
        default="/var/run/docker.sock",
        description="Docker socket path"
    )

    # Minecraft Servers
    max_servers: int = Field(default=10, description="Maximum number of servers")
    server_port_range_start: int = Field(
        default=25565,
        description="Starting port for Minecraft servers"
    )
    server_port_range_end: int = Field(
        default=25664,
        description="Ending port for Minecraft servers (supports 100 servers)"
    )
    rcon_port_range_start: int = Field(
        default=35565,
        description="Starting port for RCON"
    )
    rcon_port_range_end: int = Field(
        default=35664,
        description="Ending port for RCON"
    )

    # Backups
    backup_retention_days: int = Field(
        default=30,
        description="Days to keep backups before auto-deletion"
    )
    backup_max_size_gb: int = Field(
        default=50,
        description="Maximum total backup size in GB"
    )

    # Setup
    setup_completed: bool = Field(
        default=False,
        description="Whether initial setup wizard has been completed"
    )

    def mark_setup_complete(self):
        """Mark setup as completed (will need to persist this in DB)."""
        self.setup_completed = True


# Global settings instance
settings = Settings()
