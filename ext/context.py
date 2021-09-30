import discord

from discord.ext import commands
from typing import Optional


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
