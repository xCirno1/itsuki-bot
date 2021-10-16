import discord
import re

from argparse import ArgumentParser
from collections.abc import Iterable as It
from discord.ext import commands
from typing import Optional, Union, Iterable

from ext.context import Context
from ext.errors import NotAllowed

BASE_REASON: str = "No Reason Provided."


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def check_state(member: discord.Member, target: Union[Iterable[discord.Member], discord.Member], fail: bool = True):
        if isinstance(target, It):
            if all(member.top_role > m.top_role for m in target):
                return True
        if member.top_role > target.top_role:
            return True
        if fail:
            raise NotAllowed(f"Your role is lower or equals to {target}")
        else:
            return False

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx: Context,
                   member: commands.Greedy[discord.Member],
                   *, reason: Optional[str] = BASE_REASON) -> Optional[discord.Message]:
        """Kick member(s) from the server. You can provide multiple members too."""
        self.check_state(ctx.author, member)
        message = await ctx.send(f"Are you sure you want to kick {member}?\n\nReason:\n{reason}")
        if await ctx.send_confirmation(message):
            if isinstance(member, Iterable):
                for m in member:
                    await m.kick(reason=reason)
                    user = self.bot.get_user(m.id)
                    await user.send(f"You are kicked from {ctx.guild}!\n\nReason:\n{reason}")
                return await ctx.send(f"Kicked all {ctx.author}!")
            user = self.bot.get_user(member.id)
            await member.kick(reason=reason)
            await ctx.send(f"Kicked {ctx.author}!")
            await user.send(f"You are kicked from {ctx.guild}!\n\nReason:\n{reason}")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx: Context,
                  member: commands.Greedy[discord.Member],
                  *, reason: Optional[str] = BASE_REASON) -> Optional[discord.Message]:
        """Ban a member(s) from the server. You can provide multiple members too."""
        self.check_state(ctx.author, member)
        message = await ctx.send(f"Are you sure you want to ban {member}?\n\nReason:\n{reason}")
        if await ctx.send_confirmation(message):
            if isinstance(member, Iterable):
                for m in member:
                    await m.ban(reason=reason)
                    user = self.bot.get_user(m.id)
                    await user.send(f"You are banned from {ctx.guild}!\n\nReason:\n{reason}")
                return await ctx.send(f"Banned all {member}!")
            user = self.bot.get_user(member.id)
            await member.ban(reason=reason)
            await ctx.send(f"Banned {member}!")
            await user.send(f"You are banned from {ctx.guild}!\n\nReason:\n{reason}")

    @commands.command()
    async def nick(self, ctx: Context,
                   member: commands.Greedy[discord.Member] = None,
                   new_name: Optional[str] = None,
                   reason: Optional[str] = BASE_REASON
                   ) -> Optional[discord.Message]:
        """Change the nickname of member(s). You can provide multiple members too.
        There are 2 logics implemented here
        1. If the member role's is higher than yours or you don't provide any members,
        your **own** nickname will be changed to new_name.
        2. If no new_name is provided, the member or your nickname will be resetted."""
        if ctx.author.guild_permissions.manage_nicknames and member:
            raise commands.MissingPermissions("manage_nicknames")
        member: discord.Member = member or ctx.author
        if self.check_state(ctx.author, member):
            if isinstance(member, Iterable):
                for m in member:
                    await m.edit(nick=new_name, reason=reason)
            else:
                await member.edit(nick=new_name, reason=reason)
        else:
            member = ctx.author
            await member.edit(nick=new_name, reason=reason)
        if new_name:
            return await ctx.send(f"Changed nick of {member.display_name} to {new_name}")
        await ctx.send(f"Resetted nick of {member}.")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx: Context, amount: Optional[int] = 2, *, checks: str = None):
        """
        Purges x amount of message with a specific check if given.
        **All supported flags:**
        `-user`: A mention or name of the user to remove.
        `-contains`: A substring to search for in the message.
        `-starts`: A substring to search if the message starts with.
        `-ends`: A substring to search if the message ends with.
        `-search`: How many messages to search. Default 100. Max 2000.
        `-after`: Messages must come after this message ID.
        `-before`: Messages must come before this message ID.

        Flag only:
        `-bot`: Check if it's a bot user.
        `-embeds`: Check if the message has embeds.
        `-files`: Check if the message has attachments.
        `-emoji`: Check if the message has custom emoji.
        `-reactions`: Check if the message has reactions
        `-or`: Use logical OR for all options.
        `-not`: Use logical NOT for all options.
        """
        await ctx.message.delete()
        if not checks:
            return await ctx.channel.purge(limit=amount)

        parser = ArgumentParser(add_help=False, allow_abbrev=False)
        parser.add_argument('-user', nargs='+')
        parser.add_argument('-contains', nargs='+')
        parser.add_argument('-starts', nargs='+')
        parser.add_argument('-ends', nargs='+')
        parser.add_argument('-or', action='store_true', dest='or_')
        parser.add_argument('-not', action='store_true', dest='not_')
        parser.add_argument('-emoji', action='store_true')
        parser.add_argument('-bot', action='store_const', const=lambda m: m.author.bot)
        parser.add_argument('-embeds', action='store_const', const=lambda m: len(m.embeds))
        parser.add_argument('-files', action='store_const', const=lambda m: len(m.attachments))
        parser.add_argument('-reactions', action='store_const', const=lambda m: len(m.reactions))
        parser.add_argument('-after', type=int)
        parser.add_argument('-before', type=int)
        args = parser.parse_args(checks.split())

        predicates = []
        if args.bot:
            predicates.append(args.bot)

        if args.embeds:
            predicates.append(args.embeds)

        if args.files:
            predicates.append(args.files)

        if args.reactions:
            predicates.append(args.reactions)

        if args.emoji:
            custom_emoji = re.compile(r'<:(\w+):(\d+)>')
            predicates.append(lambda m: custom_emoji.search(m.content))

        if args.user:
            users = []
            converter = commands.MemberConverter()
            for u in args.user:
                try:
                    user = await converter.convert(ctx, u)
                    users.append(user)
                except Exception as e:
                    return await ctx.send(str(e))

            predicates.append(lambda m: m.author in users)

        if args.contains:
            predicates.append(lambda m: any(sub in m.content for sub in args.contains))

        if args.starts:
            predicates.append(lambda m: any(m.content.startswith(s) for s in args.starts))

        if args.ends:
            predicates.append(lambda m: any(m.content.endswith(s) for s in args.ends))

        op = all if not args.or_ else any

        def predicate(m):
            r = op(p(m) for p in predicates)
            if args.not_:
                return not r
            return r

        purged = await ctx.channel.purge(limit=amount, check=predicate, before=args.before, after=args.after)
        await ctx.alert(f"Purged {len(purged)} messages!")


def setup(bot):
    bot.add_cog(Moderation(bot))
