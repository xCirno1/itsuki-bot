import datetime

from discord.ext import tasks, commands

from enums import Channels, Roles


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @tasks.loop(minutes=1)
    async def donation_reminder(self):
        if datetime.datetime.utcnow().strftime("%H:%M") == "00:00":
            channel = await self.bot.get_channel(Channels.donation)
            await channel.send(f"<@&{Roles.clan_members}> Don't forget to donate!!")


def setup(bot):
    bot.add_cog(Tasks(bot))
