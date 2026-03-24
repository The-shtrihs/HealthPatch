from urllib.parse import urlencode

import httpx

from src.core.config import get_settings
from src.core.exceptions import OAuthProviderError
from src.repositories.oauth_state import OAuthStateRepository
from src.repositories.user import UserRepository
from src.schemas.auth import TokenResponse
from src.schemas.oauth import UserInfo
from src.services.auth import AuthService


class OAuthService:
    def __init__(
        self, 
        auth_service: AuthService, 
        oauth_state_repo: OAuthStateRepository, 
        user_repo: UserRepository
    ):
        self.settings = get_settings()
        self.auth_service = auth_service
        self.oauth_state_repo = oauth_state_repo
        self.user_repo = user_repo

    async def verify_oauth_state(self, state: str, provider: str, ip_address: str | None = None) -> str | None:
        data = await self.oauth_state_repo.validate_and_consume(state)
        if not data:
            return None
        if data.provider != provider:
            return None
        if data.ip_address and data.ip_address != ip_address:
            return None
        
        return data.redirect_after

    async def get_google_auth_url(self, redirect_after: str = "/", ip_address: str | None = None) -> str:
        state = await self.oauth_state_repo.create(provider="google", redirect_after=redirect_after, ip_address=ip_address)
        params = {
            "client_id": self.settings.google_client_id,
            "redirect_uri": f"{self.settings.backend_url}/oauth/google/callback",
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }

        return f"{self.settings.google_auth_url}?{urlencode(params)}"

    async def exchange_google_code(self, code: str) -> UserInfo:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                self.settings.google_token_url,
                data={
                    "code": code,
                    "client_id": self.settings.google_client_id,
                    "client_secret": self.settings.google_client_secret,
                    "redirect_uri": f"{self.settings.backend_url}/oauth/google/callback",
                    "grant_type": "authorization_code",
                },
            )
            token_data = token_response.json()
            if "error" in token_data:
                raise OAuthProviderError(f"Google error: {token_data.get('error_description', 'Unknown error')}")

            google_access_token = token_data["access_token"]
            userinfo_response = await client.get(self.settings.google_userinfo_url, headers={"Authorization": f"Bearer {google_access_token}"})

            userinfo = userinfo_response.json()

            return UserInfo(
                provider="google",
                provider_id=userinfo["id"],
                email=userinfo["email"],
                name=userinfo.get("name", userinfo["email"].split("@")[0]),
                avatar_url=userinfo.get("picture"),
                is_verified=userinfo.get("email_verified", False),
            )

    async def get_github_auth_url(self, redirect_after: str = "/", ip_address: str | None = None) -> str:
        state = await self.oauth_state_repo.create(provider="github", redirect_after=redirect_after, ip_address=ip_address)
        params = {
            "client_id": self.settings.github_client_id,
            "redirect_uri": f"{self.settings.backend_url}/oauth/github/callback",
            "scope": "read:user user:email",
            "state": state,
            "allow_signup": "true",
        }
        return f"{self.settings.github_auth_url}?{urlencode(params)}"

    async def exchange_github_code(self, code: str) -> UserInfo:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                self.settings.github_token_url,
                data={
                    "code": code,
                    "client_id": self.settings.github_client_id,
                    "client_secret": self.settings.github_client_secret,
                    "redirect_uri": f"{self.settings.backend_url}/oauth/github/callback",
                },
                headers={"Accept": "application/json"},
            )
            token_data = token_response.json()
            if "error" in token_data:
                raise OAuthProviderError(f"GitHub error: {token_data.get('error_description', 'Unknown error')}")

            github_access_token = token_data["access_token"]
            headers = {"Authorization": f"Bearer {github_access_token}"}
            user_response = await client.get(self.settings.github_user_url, headers=headers)
            userinfo = user_response.json()

            email = userinfo.get("email")
            if not email:
                emails_response = await client.get(self.settings.github_emails_url, headers=headers)
                emails = emails_response.json()
                primary = next((e for e in emails if e["primary"]), emails[0])
                email = primary["email"]

            return UserInfo(
                provider="github",
                provider_id=str(userinfo["id"]),
                email=email,
                name=userinfo.get("name", userinfo["login"]),
                avatar_url=userinfo.get("avatar_url"),
                is_verified=True,
            )

    async def get_facebook_auth_url(self, redirect_after: str = "/", ip_address: str | None = None) -> str:
        state = await self.oauth_state_repo.create(provider="facebook", redirect_after=redirect_after, ip_address=ip_address)
        params = {
            "client_id": self.settings.facebook_client_id,
            "redirect_uri": f"{self.settings.backend_url}/oauth/facebook/callback",
            "scope": "email public_profile",
            "state": state,
            "response_type": "code",
        }
        return f"{self.settings.fb_auth_url}?{urlencode(params)}"

    async def exchange_facebook_code(self, code: str) -> UserInfo:
        async with httpx.AsyncClient() as client:
            token_response = await client.get(
                self.settings.fb_token_url,
                params={
                    "code": code,
                    "client_id": self.settings.facebook_client_id,
                    "client_secret": self.settings.facebook_client_secret,
                    "redirect_uri": f"{self.settings.backend_url}/oauth/facebook/callback",
                },
            )
            token_data = token_response.json()
            if "error" in token_data:
                error_msg = token_data["error"].get("message", "Unknown error")
                raise OAuthProviderError(f"Facebook error: {error_msg}")

            fb_access_token = token_data["access_token"]
            user_response = await client.get(self.settings.fb_user_url, params={"fields": "id,name,email,picture", "access_token": fb_access_token})
            userinfo = user_response.json()

            return UserInfo(
                provider="facebook",
                provider_id=userinfo["id"],
                email=userinfo.get("email"),
                name=userinfo.get("name", userinfo.get("email", "").split("@")[0]),
                avatar_url=userinfo.get("picture", {}).get("data", {}).get("url"),
                is_verified=True,
            )

    async def handle_oauth_user(self, oauth_data: UserInfo) -> TokenResponse:
        user = await self.user_repo.get_by_oauth(oauth_data.provider, oauth_data.provider_id)
        if not user:
            user = await self.user_repo.get_by_email(oauth_data.email)
            if user:
                user = await self.user_repo.update_oauth_info(user, oauth_data.provider, oauth_data.provider_id, oauth_data.avatar_url)
            else:
                user = await self.user_repo.create(
                    name=oauth_data.name,
                    email=oauth_data.email,
                    password_hash=None,
                    provider=oauth_data.provider,
                    provider_id=oauth_data.provider_id,
                    avatar_url=oauth_data.avatar_url,
                )

        access_token = self.auth_service.create_access_token(user)
        refresh_token = await self.auth_service.create_refresh_token(user, device_info=None)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.settings.access_token_expire_minutes * 60,
        )