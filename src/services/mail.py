from datetime import UTC, datetime, timedelta

import jwt
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from src.core.config import get_settings


class MailService:
    def __init__(self):
        self.settings = get_settings()
        
        self.conf = ConnectionConfig(
            MAIL_USERNAME=self.settings.smtp_username,
            MAIL_PASSWORD=self.settings.smtp_password,
            MAIL_FROM=self.settings.smtp_username,
            MAIL_PORT=self.settings.smtp_port,
            MAIL_SERVER=self.settings.smtp_host,
            MAIL_FROM_NAME="HealthPatch Support",
            MAIL_STARTTLS=True,  
            MAIL_SSL_TLS=False,  
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True
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
                raise ValueError("Invalid token purpose")
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
    
    async def send_email(self, to_email: str, subject: str, html_body: str):
        message = MessageSchema(
            subject=subject,
            recipients=[to_email], 
            body=html_body,
            subtype=MessageType.html
        )
        
        await self.fastmail.send_message(message)
    
    async def send_verification_email(self, user_id: int, user_email: str, name: str):
        token = self.create_email_token(user_id, user_email, purpose="email_verify")
        verification_link = f"{self.settings.frontend_url}/verify-email?token={token}" 
        
        html_body = f"""
        <p>Hi {name},</p>
        <p>Thank you for registering. Please click the link below to verify your email address:</p>
        <a href="{verification_link}">Verify Email</a>
        <p>If you did not create an account, please ignore this email.</p>
        """
        await self.send_email(user_email, "Email Verification", html_body)

    async def send_password_reset_email(self, user_id: int, user_email: str, name: str):
        token = self.create_email_token(user_id, user_email, purpose="password_reset")
        reset_link = f"{self.settings.frontend_url}/reset-password?token={token}"
        
        html_body = f"""
        <p>Hi {name},</p>
        <p>We received a request to reset your password. Please click the link below to set a new password:</p>
        <a href="{reset_link}">Reset Password</a>
        <p>If you did not request a password reset, please ignore this email.</p>
        """
        await self.send_email(user_email, "Password Reset Request", html_body)