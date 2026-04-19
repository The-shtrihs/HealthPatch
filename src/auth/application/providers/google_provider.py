import httpx

from src.auth.application.providers.dto import OAuthUserInfo
from src.auth.domain.errors import OAuthProviderError
from src.core.config import get_settings


class GoogleOAuthProvider:
    def __init__(self) -> None:
        self._s = get_settings()

    def get_auth_url(self, state: str) -> str:
        from urllib.parse import urlencode

        params = {
            "client_id": self._s.google_client_id,
            "redirect_uri": f"{self._s.backend_url}/oauth/google/callback",
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        return f"{self._s.google_auth_url}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> OAuthUserInfo:
        async with httpx.AsyncClient() as client:
            token_resp = await client.post(
                self._s.google_token_url,
                data={
                    "code": code,
                    "client_id": self._s.google_client_id,
                    "client_secret": self._s.google_client_secret,
                    "redirect_uri": f"{self._s.backend_url}/oauth/google/callback",
                    "grant_type": "authorization_code",
                },
            )
            token_data = token_resp.json()
            if "error" in token_data:
                raise OAuthProviderError(
                    f"Google error: {token_data.get('error_description', 'Unknown error')}"
                )

            userinfo_resp = await client.get(
                self._s.google_userinfo_url,
                headers={"Authorization": f"Bearer {token_data['access_token']}"},
            )
            u = userinfo_resp.json()

        return OAuthUserInfo(
            provider="google",
            provider_id=u["id"],
            email=u["email"],
            name=u.get("name", u["email"].split("@")[0]),
            avatar_url=u.get("picture"),
            is_verified=u.get("email_verified", False),
        )