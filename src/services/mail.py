from datetime import UTC, datetime, timedelta
from pathlib import Path

import jwt
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from src.core.config import get_settings
from src.core.exceptions import InvalidTokenError


class MailService:
    def __init__(self):
        self.settings = get_settings()
        template_folder = Path(__file__).parent.parent / "templates"
        self.conf = ConnectionConfig(
            MAIL_USERNAME=self.settings.smtp_username,
            MAIL_PASSWORD=self.settings.smtp_password,
            MAIL_FROM="the.shtrihs@gmail.com",
            MAIL_PORT=self.settings.smtp_port,
            MAIL_SERVER=self.settings.smtp_host,
            MAIL_FROM_NAME="HealthPatch Support",
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
            TEMPLATE_FOLDER=str(template_folder),
        )

        self.fastmail = FastMail(self.conf)

    def create_email_token(self, user_id: int, user_email: str, purpose: str, expire_minutes: int = None) -> str:
        if expire_minutes is None:
            expire_minutes = self.settings.email_token_expire_minutes
        payload = {
            "sub": str(user_id),
            "email": user_email,
            "purpose": purpose,
            "exp": datetime.now(UTC) + timedelta(minutes=expire_minutes),
        }
        return jwt.encode(payload, self.settings.secret_key, algorithm=self.settings.algorithm)

    def decode_email_token(self, token_value: str, expected_purpose: str) -> dict:
        try:
            payload = jwt.decode(token_value, self.settings.secret_key, algorithms=[self.settings.algorithm])
            if payload.get("purpose") != expected_purpose:
                raise InvalidTokenError("Invalid token purpose")
            return payload
        except jwt.ExpiredSignatureError:
            raise InvalidTokenError("Token has expired")
        except jwt.InvalidTokenError:
            raise InvalidTokenError("Invalid token")

    async def send_email(self, to_email: str, subject: str, template_name: str, template_body: dict):
        message = MessageSchema(
            subject=subject,
            recipients=[to_email],
            template_body=template_body,
            subtype=MessageType.html,
        )
        await self.fastmail.send_message(message, template_name=template_name)

    async def send_verification_email(self, user_id: int, user_email: str, name: str):
        token = self.create_email_token(user_id, user_email, purpose="email_verify")
        verification_link = f"{self.settings.frontend_url}/verify-email?token={token}"

        template_body = {"name": name, "link": verification_link}
        await self.send_email(
            to_email=user_email,
            subject="Welcome to Health Patch - Verify your Email",
            template_name="verify_email.html",
            template_body=template_body,
        )

    async def send_password_reset_email(self, user_id: int, user_email: str, name: str):
        token = self.create_email_token(user_id, user_email, purpose="password_reset")
        reset_link = f"{self.settings.frontend_url}/reset-password?token={token}"

        template_body = {"name": name, "link": reset_link}
        await self.send_email(
            to_email=user_email,
            subject="Health Patch - Password Reset Request",
            template_name="reset_password.html",
            template_body=template_body,
        )