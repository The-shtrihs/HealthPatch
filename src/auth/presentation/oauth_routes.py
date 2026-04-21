from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse

from src.auth.application.commands import HandleOAuthUserCommand
from src.auth.application.providers.dto import OAuthUserInfo
from src.auth.application.providers.facebook_provider import FacebookOAuthProvider
from src.auth.application.providers.github_provider import GitHubOAuthProvider
from src.auth.application.providers.google_provider import GoogleOAuthProvider
from src.auth.application.handlers.oauth import HandleOAuthUserCommandHandler
from src.auth.infrastructure.oauth_state_repository import OAuthStateData, RedisOAuthStateRepository
from src.auth.presentation.dependencies import get_oauth_handler, get_oauth_state_repo
from src.core.config import get_settings

router = APIRouter(prefix="/oauth", tags=["OAuth Authentication"])

_PROVIDERS = {
    "google": GoogleOAuthProvider,
    "github": GitHubOAuthProvider,
    "facebook": FacebookOAuthProvider,
}


@router.get("/{provider}")
async def oauth_redirect(
    provider: str,
    request: Request,
    redirect_after: str = Query("/"),
    state_repo: RedisOAuthStateRepository = Depends(get_oauth_state_repo),
):
    if provider not in _PROVIDERS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OAuth provider not supported")

    ip = request.client.host if request.client else None
    state_token = await state_repo.create(provider=provider, redirect_after=redirect_after, ip_address=ip)

    auth_url = _PROVIDERS[provider]().get_auth_url(state_token)
    return RedirectResponse(auth_url)


@router.get("/{provider}/callback")
async def oauth_callback(
    provider: str,
    request: Request,
    state: str = Query(...),
    code: str | None = Query(None),
    error: str | None = Query(None),
    state_repo: RedisOAuthStateRepository = Depends(get_oauth_state_repo),
    oauth_handler: HandleOAuthUserCommandHandler = Depends(get_oauth_handler),
):
    if provider not in _PROVIDERS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OAuth provider not supported")

    settings = get_settings()
    frontend = settings.frontend_url.rstrip("/")

    if error:
        return RedirectResponse(f"{frontend}/login?error={error}")

    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Authorization code is missing")

    ip = request.client.host if request.client else None
    state_data: OAuthStateData | None = await state_repo.validate_and_consume(state)

    if not state_data or state_data.provider != provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state (CSRF protection) or timeout",
        )

    if state_data.ip_address and state_data.ip_address != ip:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state (IP mismatch)",
        )

    oauth_info: OAuthUserInfo = await _PROVIDERS[provider]().exchange_code(code)
    handle_ouath_cmd = HandleOAuthUserCommand(
        provider=provider,
        provider_id=oauth_info.provider_id,
        email=oauth_info.email,
        name=oauth_info.name,
        avatar_url=oauth_info.avatar_url,
    )
    result = await oauth_handler.handle(handle_ouath_cmd)

    redirect_url = (
        f"{frontend}/auth/callback?access_token={result.access_token}&refresh_token={result.refresh_token}&redirect_after={state_data.redirect_after}"
    )
    return RedirectResponse(redirect_url)
