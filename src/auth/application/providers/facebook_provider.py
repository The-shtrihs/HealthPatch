import httpx

from src.auth.application.providers.dto import OAuthUserInfo
from src.auth.domain.errors import OAuthProviderError
from src.core.config import get_settings


class FacebookOAuthProvider:
    def __init__(self) -> None:
        self._s = get_settings()

    def get_auth_url(self, state: str) -> str:
        from urllib.parse import urlencode

        params = {
            "client_id": self._s.facebook_client_id,
            "redirect_uri": f"{self._s.backend_url}/oauth/facebook/callback",
            "scope": "email public_profile",
            "state": state,
            "response_type": "code",
        }
        return f"{self._s.fb_auth_url}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> OAuthUserInfo:
        async with httpx.AsyncClient() as client:
            token_resp = await client.get(
                self._s.fb_token_url,
                params={
                    "code": code,
                    "client_id": self._s.facebook_client_id,
                    "client_secret": self._s.facebook_client_secret,
                    "redirect_uri": f"{self._s.backend_url}/oauth/facebook/callback",
                },
            )
            token_data = token_resp.json()
            if "error" in token_data:
                raise OAuthProviderError(f"Facebook error: {token_data['error'].get('message', 'Unknown error')}")

            user_resp = await client.get(
                self._s.fb_user_url,
                params={
                    "fields": "id,name,email,picture",
                    "access_token": token_data["access_token"],
                },
            )
            u = user_resp.json()

        return OAuthUserInfo(
            provider="facebook",
            provider_id=u["id"],
            email=u.get("email"),
            name=u.get("name") or u.get("email", "").split("@")[0],
            avatar_url=u.get("picture", {}).get("data", {}).get("url"),
            is_verified=True,
        )
