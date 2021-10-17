from __future__ import annotations

import discord

from discord import Emoji
from discord.ext import commands
from typing import Optional, List, Union, Callable, TYPE_CHECKING

from .pagination import Paginate

if TYPE_CHECKING:
    from discord import User


class Context(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def reply(self, content: Optional[str] = None, **kwargs):
        """Make sure that the default reply does not mention the author."""
        if not kwargs.get('mention_author', None):
            kwargs['mention_author'] = False

        return await super().reply(content=content, **kwargs)

    async def send_confirmation(self, message: discord.Message = None, timeout: int = None):
        """React and wait for confirmation message's reaction to be reacted."""
        if not message:
            message = self.message
        await message.add_reaction('✅')
        await message.add_reaction('❌')
        while True:
            r, u = await self.bot.wait_for("reaction_add",
                                           check=lambda re, us: us.id == self.author.id and str(re.emoji) in (
                                               '✅', '❌') and re.message == message,
                                           timeout=timeout)

            if str(r.emoji) == "✅":
                return True
            elif str(r.emoji) == "❌":
                await message.clear_reactions()
                return False

    async def send_trash(self, message: discord.Message = None, timeout: int = None):
        """React and wait for trash reaction to be reacted then delete message."""
        if not message:
            message = self.message
        await message.add_reaction('🗑️')
        await self.bot.wait_for("reaction_add",
                                check=lambda re, us: us.id == self.author.id and str(re.emoji) == '🗑️' and re.message == message,
                                timeout=timeout)
        await message.delete()

    async def alert(self, *args, **kwargs):
        await super().send(*args, **kwargs, delete_after=10)

    def paginate(self, message=None,
                 reactions: List[Union[str, Emoji]] = None,
                 check: Callable = None, timeout: int = None,
                 user: User = None, pages=None, start_from_page: int = 0):
        cls = Paginate
        cls.from_context(self)
        return cls(message=message,
                   reactions=reactions,
                   check=check,
                   user=user,
                   pages=pages,
                   start_from_page=start_from_page,
                   timeout=timeout)
