import discord

from discord.ext import commands
from typing import Optional

from ext.context import Context


BASE_REASON: str = "No Reason Provided."


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def check_state(member: discord.Member, target: discord.Member):
        if member.top_role > target.top_role:
            return True
        raise commands.MissingPermissions(f"Your role is lower or equals to {target}")

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx: Context, member: discord.Member, *, reason: Optional[str] = BASE_REASON) -> None:
        message = await ctx.send(f"Are you sure you want to kick {member}?\n\nReason:\n{reason}")
        if await ctx.send_confirmation(message):
            await member.kick(reason=reason)
            await ctx.send(f"Kicked {ctx.author}!")
        user = self.bot.get_user(member.id)
        await user.send("You've been kicked from ")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx: Context, member: discord.Member, *, reason: Optional[str] = BASE_REASON) -> None:
        message = await ctx.send(f"Are you sure you want to ban {member}?\n\nReason:\n{reason}")

        if await ctx.send_confirmation(message):
            await member.ban(reason=reason)
            await ctx.send(f"Banned {member}!")

    @commands.command()
    async def nick(self, ctx: Context,
                   member: Optional[discord.Member] = None,
                   new_name: Optional[str] = None,
                   reason: Optional[str] = BASE_REASON
                   ) -> Optional[discord.Message]:
        if ctx.author.guild_permissions.manage_nicknames and member:
            raise commands.MissingPermissions("manage_nicknames")
        member: discord.Member = member or ctx.author
        await member.edit(nick=new_name, reason=reason)
        if new_name:
            return await ctx.send(f"Changed nick of {member.display_name} to {new_name}")
        await ctx.send(f"Resetted nick of {member}.")


def setup(bot):
    pass
