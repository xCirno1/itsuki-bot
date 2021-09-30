from ext.context import Context
from discord.ext import commands


class Listeners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_long_invoke")
    async def long_invoke(self, ctx: Context, timeout: int) -> None:
        base_message = f"{ctx.author}, command `{ctx.command}` took more than {timeout} seconds."
        await ctx.send(base_message + " Please try again.")
        self.bot.log.info(base_message)

    @commands.Cog.listener("on_command_error")
    async def command_error(self, ctx, error) -> None:
        await ctx.send(error)
        raise error


def setup(bot):
    bot.add_cog(Listeners(bot))
