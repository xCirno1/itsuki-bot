import discord

from discord.ext import commands
from typing import Dict, Coroutine, Mapping, List, Optional
from ext.decorators import cancel_long_invoke


def qualify_command(self) -> Dict[str, List[str]]:
    """
    This will be the process of arranging commands to its cog.
    """
    command_qualify_dict = {}
    for command in self.context.bot.commands:
        cog = command.cog_name if command.cog_name is not None else "No Category"
        if cog not in command_qualify_dict:
            command_qualify_dict[command.cog_name if command.cog_name is not None else "No Category"] = [command.qualified_name]
            print("a")
        else:
            command_qualify_dict[command.cog_name if command.cog_name is not None else "No Category"].append(command.qualified_name)
    return command_qualify_dict


class MyHelp(commands.HelpCommand):
    @cancel_long_invoke()
    async def send_bot_help(self, mapping: Mapping[Optional[commands.Cog], List[commands.Command]] = None) -> Coroutine:
        """Sends default help message."""
        _to = self.get_destination()
        cmds = qualify_command(self)
        embed = discord.Embed(title="Help command!",
                              description="All commands that are accessible are shown below!",
                              colour=0xff6666
                              )
        for k, v in cmds.items():
            embed.add_field(name=k, value=' '.join(v))
        embed.set_image(
            url="https://cdn.discordapp.com/attachments/764033250749579284"
                "/829891083005329408/Untitled255.png")
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/826698396131393546"
                "/829891715850436668/a21410c1b7703c9fd35270f6f751006e.png")
        embed.set_footer(text="Type i!help <command name/category>")
        return await _to.send(embed=embed)

    @cancel_long_invoke()
    async def send_command_help(self, command: commands.Command) -> Coroutine:
        """Sends command's specific help message."""
        _to = self.get_destination()
        embed = discord.Embed(title=f"Displaying command: {command.name}", description=command.callback.__doc__ if command.callback.__doc__ else "No description for this command currently.", colour=0xff6666)
        if command.aliases:
            embed.add_field(name="Aliases", value=', '.join(command.aliases))
        if command.signature:
            embed.add_field(name="Usage", value=f"{self.context.bot.command_prefix}{command.name} {command.signature}")
        embed.set_footer(text="Type i!help <command name/category>")
        return await _to.send(embed=embed)

    @cancel_long_invoke()
    async def send_cog_help(self, cog: commands.Cog) -> Coroutine:
        """Sends cog/category specific help message."""
        embed = discord.Embed(title=f"Displaying Category: {cog.qualified_name}",
                              description=f"{cog.description}\n\nCommands: {cog.get_commands()}")
        _to = self.get_destination()
        return await _to.send(embed=embed)


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        help_command = MyHelp()
        help_command.cog = self
        bot.help_command = help_command


def setup(bot):
    bot.add_cog(Help(bot))
