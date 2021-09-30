import asyncio
import functools
import enums
import discord

from discord.ext.commands import Context


def cancel_long_invoke(timeout: int = 1):
    """This decorator will cancel a running function if it runs too long."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                if func.__qualname__.startswith("MyHelp"):
                    loop = args[0].context.bot.loop
                else:
                    loop = args[0].bot.loop
                task = loop.create_task(asyncio.wait_for(func(*args, **kwargs), timeout=timeout))
                return await task

            except asyncio.TimeoutError:
                if func.__qualname__.startswith("MyHelp"):
                    args[0].context.bot.dispatch("long_invoke", args[0], timeout)
                else:
                    args[1].bot.dispatch("long_invoke", args[1], timeout)

        return wrapper
    return decorator


def check_access(Type: enums):
    """Check if an attribute of type :attr:`Type.type` is in :attr:`type.__iter__`."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if isinstance(context := args[0], Context):
                ...
            else:
                context = args[1]
            if not Type.abc:
                bucket_type = getattr(discord, Type.type)
            else:
                bucket_type = getattr(discord.abc, Type.type)
            for k in context.message.__slots__:
                try:
                    if isinstance(attr := (getattr(context.message, k)), bucket_type):
                        if attr.id in Type:
                            return await context.bot.loop.create_task(func(*args, **kwargs))
                except AttributeError:
                    pass
            return
        return wrapper
    return decorator


def send_typing(seconds: int = 3):  # TODO: Make option whether the command should be run simultaneously with typing or not
    """Sends a typing indicator for x seconds before the commands is invoked."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            with args[0].typing():
                await asyncio.sleep(seconds)
                task = args[0].bot.loop.create_task(func(*args, **kwargs))
            return task
        return wrapper
    return decorator
