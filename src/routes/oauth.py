from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse

from src.core.config import get_settings
from src.routes.dependencies import get_oauth_service
from src.schemas.auth import TokenResponse
from src.schemas.oauth import UserInfo
from src.services.oauth import OAuthService

router = APIRouter(prefix="/oauth", tags=["OAuth Authentication"])

SUPPORTED_PROVIDERS = ["google", "github", "facebook"]


@router.get("/{provider}")
async def oauth_redirect(provider: str, request: Request, redirect_after: str = Query("/"), oauth_service: OAuthService = Depends(get_oauth_service)):
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OAuth provider not supported")

    ip_address = request.client.host if request.client else None

    if provider == "google":
        auth_url = await oauth_service.get_google_auth_url(redirect_after, ip_address)
    elif provider == "github":
        auth_url = await oauth_service.get_github_auth_url(redirect_after, ip_address)
    elif provider == "facebook":
        auth_url = await oauth_service.get_facebook_auth_url(redirect_after, ip_address)

    return RedirectResponse(auth_url)


@router.get("/{provider}/callback")
async def oauth_callback(
    provider: str,
    request: Request,
    state: str = Query(...),
    code: str | None = Query(None),
    error: str | None = Query(None),
    oauth_service: OAuthService = Depends(get_oauth_service),
    settings=Depends(get_settings),
):
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OAuth provider not supported")

    frontend_url = settings.frontend_url.rstrip("/")

    if error:
        return RedirectResponse(f"{frontend_url}/login?error={error}")

    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Authorization code is missing")

    ip_address = request.client.host if request.client else None

    redirect_after = await oauth_service.verify_oauth_state(state, provider, ip_address)

    if not redirect_after:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state (CSRF protection) or timeout")

    if provider == "google":
        oauth_data: UserInfo = await oauth_service.exchange_google_code(code)
    elif provider == "github":
        oauth_data: UserInfo = await oauth_service.exchange_github_code(code)
    elif provider == "facebook":
        oauth_data: UserInfo = await oauth_service.exchange_facebook_code(code)

    token: TokenResponse = await oauth_service.handle_oauth_user(oauth_data)

    redirect_url = (
        f"{frontend_url}/auth/callback?access_token={token.access_token}&refresh_token={token.refresh_token}&redirect_after={redirect_after}"
    )

    return RedirectResponse(redirect_url)
