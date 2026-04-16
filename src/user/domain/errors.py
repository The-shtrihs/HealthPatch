class UserDomainError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class UserNotFoundError(UserDomainError):
    def __init__(self, user_id: int | None = None):
        msg = f"User {user_id} not found" if user_id else "User not found"
        super().__init__(msg)