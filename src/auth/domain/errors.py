class AuthDomainError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class EmailAlreadyExistsError(AuthDomainError):
    def __init__(self):
        super().__init__("Email already registered")


class EmailAlreadyVerifiedError(AuthDomainError):
    def __init__(self):
        super().__init__("Email is already verified")


class InvalidCredentialsError(AuthDomainError):
    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(message)


class InvalidTokenError(AuthDomainError):
    def __init__(self, message: str = "Invalid or expired token"):
        super().__init__(message)


class UserNotFoundError(AuthDomainError):
    def __init__(self, user_id: int | str | None = None):
        msg = f"User {user_id} not found" if user_id else "User not found"
        super().__init__(msg)


class UserInactiveError(AuthDomainError):
    def __init__(self):
        super().__init__("User account is inactive or not verified")


class TwoFactorAlreadyEnabledError(AuthDomainError):
    def __init__(self):
        super().__init__("Two-factor authentication is already enabled")


class TwoFactorNotEnabledError(AuthDomainError):
    def __init__(self, message: str = "Two-factor authentication is not enabled"):
        super().__init__(message)


class InvalidTwoFactorCodeError(AuthDomainError):
    def __init__(self):
        super().__init__("Invalid or expired 2FA code")


class PasswordMismatchError(AuthDomainError):
    def __init__(self):
        super().__init__("Current password is incorrect")


class OAuthProviderError(AuthDomainError):
    def __init__(self, message: str = "OAuth provider error"):
        super().__init__(message)
