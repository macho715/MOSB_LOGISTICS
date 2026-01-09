from typing import Iterable

from fastapi import Depends, HTTPException, status

from auth import User, Role, get_current_user


def require_role(allowed_roles: Iterable[Role]):
    allowed = list(allowed_roles)

    async def role_dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Access denied. Required roles: "
                    f"{allowed}, your role: {current_user.role}"
                ),
            )
        return current_user

    return role_dependency


def require_any_role(*allowed_roles: Role):
    return require_role(list(allowed_roles))
