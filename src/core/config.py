from anyio.functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_minutes: int = 60 * 24 * 7
    email_token_expire_minutes: int = 60 * 24

    smtp_host: str = "sandbox.smtp.mailtrap.io"
    smtp_port: int = 2525
    smtp_username: str = ""
    smtp_password: str = ""

    redis_url: str = "redis://redis:6379/0"
    redis_max_connections: int = 20
    oauth_state_expire_seconds: int = 300
    cache_default_expire_seconds: int = 300
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"

    google_client_id: str = ""
    google_client_secret: str = ""

    github_client_id: str = ""
    github_client_secret: str = ""

    facebook_client_id: str = ""
    facebook_client_secret: str = ""

    google_auth_url: str = "https://accounts.google.com/o/oauth2/v2/auth"
    google_token_url: str = "https://oauth2.googleapis.com/token"
    google_userinfo_url: str = "https://www.googleapis.com/oauth2/v2/userinfo"

    github_auth_url: str = "https://github.com/login/oauth/authorize"
    github_token_url: str = "https://github.com/login/oauth/access_token"
    github_user_url: str = "https://api.github.com/user"
    github_emails_url: str = "https://api.github.com/user/emails"

    fb_auth_url: str = "https://www.facebook.com/v18.0/dialog/oauth"
    fb_token_url: str = "https://graph.facebook.com/v18.0/oauth/access_token"
    fb_user_url: str = "https://graph.facebook.com/me"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache(maxsize=None)
def get_settings() -> Settings:
    return Settings()
