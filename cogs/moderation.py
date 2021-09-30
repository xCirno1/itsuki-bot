import discord

from discord.ext import commands
from ext.context import Context


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def kick(self, ctx: Context, member: discord.Member, *, reason: str = "No Reason Provided.") -> None:
        message = await ctx.send(f"Are you sure you want to kick {member}?\n\nReason:\n{reason}")
        if await ctx.send_confirmation(message):
            await member.kick(reason=reason)


def setup(bot):
    pass
