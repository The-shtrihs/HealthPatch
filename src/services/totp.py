import base64
import io

import pyotp
import qrcode


class TotpService:
    @staticmethod
    def generate_totp_secret() -> str:
        return pyotp.random_base32()

    @staticmethod
    def verify_totp(token: str, secret: str) -> bool:
        totp = pyotp.TOTP(secret)
        return totp.verify(token)

    @staticmethod
    def get_totp_uri(secret: str, user_email: str, issuer_name: str = "HealthPatch") -> str:
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=user_email, issuer_name=issuer_name)

    @staticmethod
    def generate_qr_code_base64(uri: str) -> str:
        qr = qrcode.make(uri)
        buffer = io.BytesIO()
        qr.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
