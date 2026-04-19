from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.auth.domain.errors import (
    AuthDomainError,
    EmailAlreadyExistsError,
    EmailAlreadyVerifiedError,
    InvalidCredentialsError,
    InvalidTokenError,
    InvalidTwoFactorCodeError,
    OAuthProviderError,
    PasswordMismatchError,
    TwoFactorAlreadyEnabledError,
    TwoFactorNotEnabledError,
    UserInactiveError,
    UserNotFoundError,
)

_ERROR_MAP: dict[type[AuthDomainError], tuple[int, str]] = {
    EmailAlreadyExistsError:      (409, "EMAIL_ALREADY_EXISTS"),
    EmailAlreadyVerifiedError:    (400, "EMAIL_ALREADY_VERIFIED"),
    InvalidCredentialsError:      (401, "INVALID_CREDENTIALS"),
    InvalidTokenError:            (401, "INVALID_TOKEN"),
    UserNotFoundError:            (404, "NOT_FOUND"),
    UserInactiveError:            (403, "USER_INACTIVE"),
    TwoFactorAlreadyEnabledError: (409, "2FA_ALREADY_ENABLED"),
    TwoFactorNotEnabledError:     (400, "2FA_NOT_ENABLED"),
    InvalidTwoFactorCodeError:    (401, "INVALID_2FA_CODE"),
    PasswordMismatchError:        (400, "PASSWORD_MISMATCH"),
    OAuthProviderError:           (502, "OAUTH_PROVIDER_ERROR"),
}


def setup_auth_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AuthDomainError)
    async def handle(request, exc: AuthDomainError):
        status_code, error_code = _ERROR_MAP.get(type(exc), (500, "DOMAIN_ERROR"))
        return JSONResponse(
            status_code=status_code,
            content={
                "error_code": error_code,
                "message": exc.message,
                "timestamp": datetime.now(UTC).isoformat(),
                "path": str(request.url.path),
            },
        )