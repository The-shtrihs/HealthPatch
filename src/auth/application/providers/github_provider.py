import httpx

from src.auth.application.providers.dto import OAuthUserInfo
from src.auth.domain.errors import OAuthProviderError
from src.core.config import get_settings


class GitHubOAuthProvider:
    def __init__(self) -> None:
        self._s = get_settings()

    def get_auth_url(self, state: str) -> str:
        from urllib.parse import urlencode

        params = {
            "client_id": self._s.github_client_id,
            "redirect_uri": f"{self._s.backend_url}/oauth/github/callback",
            "scope": "read:user user:email",
            "state": state,
            "allow_signup": "true",
        }
        return f"{self._s.github_auth_url}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> OAuthUserInfo:
        async with httpx.AsyncClient() as client:
            token_resp = await client.post(
                self._s.github_token_url,
                data={
                    "code": code,
                    "client_id": self._s.github_client_id,
                    "client_secret": self._s.github_client_secret,
                    "redirect_uri": f"{self._s.backend_url}/oauth/github/callback",
                },
                headers={"Accept": "application/json"},
            )
            token_data = token_resp.json()
            if "error" in token_data:
                raise OAuthProviderError(f"GitHub error: {token_data.get('error_description', 'Unknown error')}")

            headers = {"Authorization": f"Bearer {token_data['access_token']}"}
            user_resp = await client.get(self._s.github_user_url, headers=headers)
            u = user_resp.json()

            email: str | None = u.get("email")
            if not email:
                emails_resp = await client.get(self._s.github_emails_url, headers=headers)
                emails = emails_resp.json()
                primary = next((e for e in emails if e["primary"]), emails[0])
                email = primary["email"]

        return OAuthUserInfo(
            provider="github",
            provider_id=str(u["id"]),
            email=email,
            name=u.get("name") or u["login"],
            avatar_url=u.get("avatar_url"),
            is_verified=True,
        )
