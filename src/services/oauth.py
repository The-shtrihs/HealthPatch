import secrets
from urllib.parse import urlencode

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.repositories.user import UserRepository
from src.schemas.auth import LoginResponse
from src.schemas.oauth import UserInfo
from src.services.auth import AuthService


class OAuthService:
    def __init__(self, db: AsyncSession, auth_service: AuthService):
        self.settings = get_settings()
        self.oauth_states: dict[str, str] = {}
        self.db = db
        self.auth_service = auth_service

    def generate_oauth_state(self, provider: str) -> str:
        state = secrets.token_urlsafe(32)
        self.oauth_states[state] = provider
        return state

    def verify_oauth_state(self, state: str, provider: str) -> bool:
        stored_provider = self.oauth_states.get(state)
        return stored_provider == provider

    def get_google_auth_url(self) -> str:
        state = self.generate_oauth_state("google")
        params = {
            "client_id": self.settings.google_client_id,
            "redirect_uri": f"{self.settings.backend_url}/auth/google/callback",
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
                    "redirect_uri": f"{self.settings.backend_url}/auth/google/callback",
                    "grant_type": "authorization_code",
                },
            )
            token_data = token_response.json()
            if "error" in token_data:
                raise Exception(f"Error exchanging code: {token_data['error_description']}")

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

    def get_github_auth_url(self) -> str:
        state = self.generate_oauth_state("github")
        params = {
            "client_id": self.settings.github_client_id,
            "redirect_uri": f"{self.settings.backend_url}/auth/github/callback",
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
                    "redirect_uri": f"{self.settings.backend_url}/auth/github/callback",
                },
                headers={"Accept": "application/json"},
            )
            token_data = token_response.json()
            if "error" in token_data:
                raise Exception(f"Error exchanging code: {token_data['error_description']}")

            github_access_token = token_data["access_token"]
            headers={"Authorization": f"Bearer {github_access_token}"}
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

    def get_facebook_auth_url(self) -> str:
        state = self.generate_oauth_state("facebook")
        params = {
            "client_id": self.settings.facebook_client_id,
            "redirect_uri": f"{self.settings.backend_url}/auth/facebook/callback",
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
                    "redirect_uri": f"{self.settings.backend_url}/auth/facebook/callback",
                },
            )
            token_data = token_response.json()
            if "error" in token_data:
                raise Exception(f"Error exchanging code: {token_data['error']['message']}")

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

    async def handle_oauth_user(self, oauth_data: UserInfo) -> LoginResponse:
        user = await UserRepository.get_by_oauth(self.db, oauth_data.provider, oauth_data.provider_id)
        if not user:
            user = await UserRepository.get_by_email(self.db, oauth_data.email)
            if user:
                user = await UserRepository.update_oauth_info(self.db, user, oauth_data.provider, oauth_data.provider_id, oauth_data.avatar_url)
            else:
                user = await UserRepository.create(
                    db=self.db,
                    name=oauth_data.name,
                    email=oauth_data.email,
                    password_hash=self.auth_service.hash_password(secrets.token_urlsafe(32)),
                    provider=oauth_data.provider,
                    provider_id=oauth_data.provider_id,
                    avatar_url=oauth_data.avatar_url
                )

            access_token = self.auth_service.create_access_token(user)
            refresh_token = await self.auth_service.create_refresh_token(user, device_info=None)

            return LoginResponse(
                token_response={
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer",
                    "expires_in": self.settings.access_token_expire_minutes * 60,
                },
                name=user.name,
                email=user.email,
            )
