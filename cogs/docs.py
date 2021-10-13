import discord
import inspect

from discord.ext import commands
from ext.decorators import cancel_long_invoke
from ext.utils import remove


class Info(commands.Cog, name="Info"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["d", "rtfm"])
    @cancel_long_invoke()
    async def docs(self, ctx, *, query: str = None):
        """Return docs query from discord.py (look at https://discordpy.readthedocs.io/en/stable/api.html)
         for more information"""
        if query is None:
            return await ctx.send("Please provide a discord.py class or module or attribute to match!")
        if query.startswith("Bot"):
            query = "discord.ext.commands."+query

        try:
            if query.split(".")[0] not in ["discord", "tasks", "Bot", "commands"]:
                raise AttributeError
            newline = "\n"
            dot = "."
            query = "tasks." + ".".join(query.split(".")[3:] if len(query.split(".")) > 3 else "tasks") if "tasks" in query else query
            r = eval(query).__doc__.replace("|coro|", "This function is a [coroutine.](https://docs.python.org/3/library/asyncio-task.html#coroutine)").replace(":class:", "") if eval(query).__doc__ is not None else "None"
            e = r[:400] + "..."
            url = "ext/commands/" if 'commands' in query else "ext/tasks/"
            await ctx.send(embed=discord.Embed(title=query,
                                               url=f"https://discordpy.readthedocs.io/en/stable/"
                                                   f"{'' if 'commands' not in query and 'tasks' not in query else url}{'index' if 'tasks' in query else 'api'}.html#{remove(query, '.discord') if inspect.isclass(query) else query if 'discord' in query else 'discord.ext.' + query}",
                                               description=f"```py\n{query.split('.')[-1]}{inspect.signature(eval(query))}```\n{(e.split(f'Attributes{newline}')[0]).replace('`.', f'`{dot.join(query.split(dot)[2:-1]) + dot}').split(f'Parameters{newline}')[0].replace(':meth:`', f'`{query.split(dot)[-2] + dot}').replace('..', '').replace('::', ':').replace('versionadded', 'Version added')}",
                                               color=self.bot.base_color))
        except AttributeError:
            await ctx.send("No documentation found!")
        except TypeError:
            await ctx.send("This attribute/module exists but doesn't seem to have any explanation.")


def setup(bot):
    bot.add_cog(Info(bot))
