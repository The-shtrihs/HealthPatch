# app/utils/cache_decorator.py
import functools
from collections.abc import Callable


def cached(
    ttl: int = 300,
    key_prefix: str | None = None,
    skip_cache_if: Callable[..., bool] | None = None,
):

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if skip_cache_if and skip_cache_if(*args, **kwargs):
                return await func(*args, **kwargs)
            
            cache_repo = kwargs.get("cache_repo")

            cache_key = cache_repo.make_key(key_prefix or func.__qualname__, *args, **kwargs.values())

            cached_value = await cache_repo.get_or_set(
                cache_key,
                lambda: func(*args, **kwargs),
                ttl=ttl,
            )
            return cached_value

        async def invalidate(*args, **kwargs):
            cache_repo = kwargs.get("cache_repo")
            cache_key = cache_repo.make_key(key_prefix or func.__qualname__, *args, **kwargs.values())
            await cache_repo.invalidate(cache_key)

        wrapper.invalidate = invalidate
        return wrapper

    return decorator