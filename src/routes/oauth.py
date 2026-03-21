from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse

from src.routes.dependencies import get_oauth_service
from src.schemas.auth import TokenResponse
from src.schemas.oauth import UserInfo
from src.services.oauth import OAuthService

router = APIRouter(prefix="/oauth", tags=["OAuth Authentication"])


@router.get("/google")
async def google_oauth_redirect(oauth_service: OAuthService = Depends(get_oauth_service)):
    auth_url = oauth_service.get_google_auth_url()
    return RedirectResponse(auth_url)


@router.get("/google/callback")
async def google_callback(
    code: str = Query(...),
    state: str = Query(...),
    oauth_service: OAuthService = Depends(get_oauth_service),
):
    if not oauth_service.verify_oauth_state(state, "google"):
        raise HTTPException(status_code=400, detail="Invalid state (CSRF protection)")
    oauth_data: UserInfo = await oauth_service.exchange_google_code(code)
    token: TokenResponse = await oauth_service.handle_oauth_user(oauth_data)

    redirect_url = f"{oauth_service.settings.frontend_url}/auth/callback?access_token={token.access_token}&refresh_token={token.refresh_token}"

    return RedirectResponse(redirect_url)


@router.get("/github")
async def github_oauth_redirect(oauth_service: OAuthService = Depends(get_oauth_service)):
    auth_url = oauth_service.get_github_auth_url()
    return RedirectResponse(auth_url)


@router.get("/github/callback")
async def github_callback(
    code: str = Query(...),
    state: str = Query(...),
    oauth_service: OAuthService = Depends(get_oauth_service),
):
    if not oauth_service.verify_oauth_state(state, "github"):
        raise HTTPException(status_code=400, detail="Invalid state (CSRF protection)")
    oauth_data: UserInfo = await oauth_service.exchange_github_code(code)
    token: TokenResponse = await oauth_service.handle_oauth_user(oauth_data)

    redirect_url = f"{oauth_service.settings.frontend_url}/auth/callback?access_token={token.access_token}&refresh_token={token.refresh_token}"

    return RedirectResponse(redirect_url)


@router.get("/facebook")
async def facebook_oauth_redirect(oauth_service: OAuthService = Depends(get_oauth_service)):
    auth_url = oauth_service.get_facebook_auth_url()
    return RedirectResponse(auth_url)


@router.get("/facebook/callback")
async def facebook_callback(
    code: str = Query(...),
    state: str = Query(...),
    oauth_service: OAuthService = Depends(get_oauth_service),
):
    if not oauth_service.verify_oauth_state(state, "facebook"):
        raise HTTPException(status_code=400, detail="Invalid state (CSRF protection)")
    oauth_data: UserInfo = await oauth_service.exchange_facebook_code(code)
    token: TokenResponse = await oauth_service.handle_oauth_user(oauth_data)

    redirect_url = f"{oauth_service.settings.frontend_url}/auth/callback?access_token={token.access_token}&refresh_token={token.refresh_token}"

    return RedirectResponse(redirect_url)
