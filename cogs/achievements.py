import sqlite3
import typing
import discord
import datetime

from typing import Any
from discord.ext import commands

from enums import Channels, Members
from ext.utils import romanize
from ext.decorators import cancel_long_invoke
from ext.context import Context

con = sqlite3.connect("achievements.db")
cur = con.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS achievements(id INTEGER PRIMARY KEY AUTOINCREMENT, acc_id INT, message_count INT, message_deleted INT, bump_count INT, completed TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS progress(id INTEGER PRIMARY KEY AUTOINCREMENT, acc_id INT, happy_messaging INT, message_destroyer INT, advertisement INT)")
con.commit()

# to add: maxed out
query_dict = {"happy messaging!": "message_count", "message destroyer": "message_deleted", "advertisement!": "bump_count", "maxed out!": "level_count"}
desc_dict = {"happy messaging!": "Send x messages", "message destroyer": "Delete x messages", "advertisement!": "Bump x times successfully.", "maxed out!": "Reach level x"}
lev_dict = {"happy messaging!": [1000, 10000, 50000], "message destroyer": [50, 250, 1000], "advertisement!": [25, 100, 250], "maxed out!": [100]}


class Achievements(commands.Cog):
    def __init__(self, bot=None):
        self.bot = bot

# internal methods
    @staticmethod
    def _index(_dict, val) -> Any:
        """Returns a key with given value."""
        try:
            return list(_dict.keys())[list(_dict.values()).index(val)]
        except ValueError:
            return val

    def _parse_achievement(self, col_or_ach, obj: typing.Union[discord.Member, int] = None, level=None) -> str:
        """Get the level and description of an achievement."""
        _to = self._index(query_dict, col_or_ach)
        prog = self.parse_progress(col_or_ach)
        if isinstance(obj, discord.Member):
            obj = obj.id
        if not level:
            cur.execute(f"SELECT {prog} FROM progress WHERE acc_id = {obj}")
            level = cur.fetchone()[0]
        req = desc_dict[_to]
        limit = lev_dict[_to][level - 1]
        return req.replace("x", str(limit))

    def parse_progress(self, col_or_ach) -> str:
        """Get the name of progress database's row from a value."""
        col_or_ach = col_or_ach.lower()
        _to = self._index(query_dict, col_or_ach)
        return _to.replace(" ", "_").replace("!", "")

    def all_achievement(self, col_or_ach, obj) -> dict:
        _to = {}
        d = self._index(query_dict, col_or_ach)
        for i in range(1, 4):
            v = self._parse_achievement(d, obj, i)
            k = romanize(i)
            _to[k] = v
        return _to

    def _send_message(self, obj, achievement) -> None:
        """Send completed/finished message in level_up channel."""
        channel = self.bot.get_channel(Channels.bot_test)
        self.bot.loop.create_task(channel.send(f"<@{obj}> has completed an achievement: {achievement}"))

    def _get_max(self, obj, col_or_ach):
        # gets the max level
        x = self._index(query_dict, col_or_ach)
        p = self.parse_progress(x)
        cur.execute(f"SELECT {p} FROM progress WHERE acc_id = {obj}")
        count = cur.fetchone()[0]
        try:
            return lev_dict[x][count - 1]
        except KeyError:
            pass

    def _check_level(self, obj, col):
        """check if current count is greater than max level then level up"""
        achievement = self._index(query_dict, col)
        x = self.parse_progress(achievement)
        cur.execute(f"SELECT {col} FROM achievements WHERE acc_id='{obj}'")
        r = cur.fetchone()[0]
        try:
            if r >= self._get_max(obj, col):
                cur.execute(f"SELECT {x} FROM progress WHERE acc_id = {obj}")
                count = cur.fetchone()[0]
                cur.execute(f"UPDATE progress SET {self.parse_progress(achievement)}={count + 1} WHERE acc_id = {obj}")
                con.commit()
                self._send_message(obj, achievement)
            else:
                pass
        except IndexError:
            self._insert_to_complete(obj, col)

    def _add_to_db(self, obj, col, by: int):
        """Add a value to a row with a specific user."""
        cur.execute(f"SELECT {col} FROM achievements WHERE acc_id='{obj}'")
        res = cur.fetchone()
        res = res[0] + by
        cur.execute(f"UPDATE achievements SET {col}={res} WHERE acc_id='{obj}'")
        con.commit()
        cur.execute(f"SELECT {col} FROM achievements WHERE acc_id='{obj}'")
        self._check_level(obj, col)

    @staticmethod
    def _check_id_in_db(obj):
        """Check if the user exists in database."""
        cur.execute("SELECT acc_id FROM achievements")
        r = cur.fetchall()
        if (obj, ) not in r:
            cur.execute("INSERT INTO achievements(acc_id, message_count, message_deleted, bump_count, completed) VALUES (?, 1, 0, 0, 'None')", (obj,))
            cur.execute("INSERT INTO progress(acc_id, happy_messaging, message_destroyer, advertisement) VALUES (?, 1, 1, 1)", (obj,))
            con.commit()
        return True

    def _check_completed(self, obj, col_or_ach):
        """Check if the achievement is already completed (or exist in db)."""
        _to = self._index(query_dict, col_or_ach)
        cur.execute("SELECT completed FROM achievements WHERE acc_id=?", (str(obj), ))
        r: str = cur.fetchone()[0]
        if r is None:
            return False
        if any(self.parse_progress(_to) in e for e in r.split(",")):
            return True

    def _insert_to_complete(self, obj, col_or_ach):
        """Insert to completed achievement db list if passed the requirement."""
        _to = self._index(query_dict, col_or_ach)
        parsed = self.parse_progress(_to)
        time = datetime.datetime.now().strftime("%a, %d %b %y %H:%M")
        if self._check_completed(obj, parsed):
            return
        cur.execute("SELECT completed FROM achievements WHERE acc_id=?", (str(obj),))
        try:
            r = cur.fetchone()[0].split(",")
            if 'None' not in r:
                r.append(f"{parsed} {time}")
            else:
                r = [f"{parsed} {time}"]
        except AttributeError:
            r = [f"{parsed} {time}"]
        cur.execute("UPDATE achievements SET completed=? WHERE acc_id=?", (",".join(r), obj))
        con.commit()

# start
    @commands.Cog.listener("on_message")
    async def achievements(self, message):
        if not message.author.bot:
            if self._check_id_in_db(message.author.id):
                self._add_to_db(message.author.id, "message_count", 1)

    @commands.Cog.listener("on_message_delete")
    async def message_destroyer(self, message):
        if not message.author.bot:
            self._add_to_db(message.author.id, "message_deleted", 1)

    @commands.Cog.listener("on_message")
    async def advertisement(self, message):
        if not message.author.bot:
            if message.channel.id == Channels.promote and message.content.startswith("!d bump"):
                msg = await self.bot.wait_for("message", check=lambda m: m.author.id == Members.disboard and m.channel.id == Channels.promote)
                for embed in msg.embeds:
                    if "Bump done" in embed.description:
                        self._add_to_db(message.author.id, "bump_count", 1)

    @commands.Cog.listener("on_message")
    async def maxed_out(self, message):
        if not message.author.bot:
            if message.channel.id == Channels.level_up:
                if message.author.id == Members.arcane:
                    if message.content:
                        pass

    @commands.command(hidden=True)
    @cancel_long_invoke()
    async def refresh(self, ctx):
        # cur.execute("ALTER TABLE achievements ADD message_deleted TEXT")
        cur.execute("UPDATE achievements SET level_count=0")
        cur.execute("UPDATE progress SET maxed_out=1")
        # cur.execute("ALTER TABLE progress DROP happy_messaging")
        # cur.execute("ALTER TABLE achievements ADD level_count INT")
        # cur.execute("ALTER TABLE progress ADD maxed_out INT")
        # cur.execute("DROP TABLE achievements")
        # cur.execute("DROP TABLE progress")
        # cur.execute(f"SELECT message_deleted FROM achievements WHERE acc_id = 650447110402998302")
        # print(cur.fetchone())
        con.commit()
        await ctx.send("Refreshed!")


class AchievementCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.main = Achievements()

    @commands.command(aliases=["a", "achievement"])
    @cancel_long_invoke()
    async def achievements(self, ctx: Context, *, achievement=None):
        """Shows all accessible achievements.
        Example:
        ⠀⠀i!achievements <number/name>
        """
        if achievement is None:
            embed = discord.Embed(title="Achievements!", description="All accessible achievements are shown below!", color=0xff6666)
            for num, name in enumerate(desc_dict, 1):
                try:
                    level = self.main._get_max(ctx.author.id, name)  # noqa
                    to = desc_dict[name].replace("x", str(level))
                    name2 = name
                except IndexError:  # achievement is at maxed level
                    level = "MAX"
                    to = desc_dict[name]
                    name2 = name + ' :white_check_mark:'
                cur.execute(f"SELECT {query_dict[name]} FROM achievements WHERE acc_id = {ctx.author.id}")
                progress = cur.fetchone()[0]
                embed.add_field(name=f"{num}. {name2} ", value=f"{to} ({progress}/{level})", inline=False)
            print(type(ctx))
            return await ctx.reply(embed=embed)

        if achievement.isdigit():
            achievement = list(query_dict.keys())[int(achievement) - 1]

        cur.execute(f"SELECT {query_dict[achievement.lower()]} FROM achievements WHERE acc_id = {ctx.author.id}")
        a = cur.fetchone()
        cur.execute(f"SELECT {self.main.parse_progress(achievement.lower())} FROM progress WHERE acc_id = {ctx.author.id}")
        p = cur.fetchone()
        try:
            _max = lev_dict[achievement.lower()][p[0] - 1]
        except IndexError:
            _max = "MAXED"
        new_line = "\n"
        desc = f"{desc_dict[achievement.lower()]}\n\n**Levels:**\n" \
               f"{new_line.join([x + '. ' + y for x, y in Achievements().all_achievement(achievement.lower(), ctx.author.id).items()])}"
        embed = discord.Embed(title=f"{achievement} {'Completed! :white_check_mark:' if self.main._check_completed(ctx.author.id, achievement) else ''}", description=desc, color=0xff6666)  # noqa
        v = f"Level: {p[0] if p[0] < 4 else 'Completed!'} " \
            f"{'(' + self.main._parse_achievement(query_dict[achievement.lower()], ctx.author.id) + ')' if isinstance(_max, int) else ''}" \
            f"```py\n{'▇' * (round(a[0]/_max * 20)) + '  ' * (round((_max - a[0])/_max * 20)) + '|' if isinstance(_max, int) else ''} {a[0]}/{_max}```"  # noqa
        embed.add_field(name="Progress: ", value=v)
        await ctx.reply(embed=embed)

    @commands.command()
    async def baninfo(self, ctx, member: discord.User):
        for i in await ctx.guild.bans():
            if i.user.id == member.id:
                await ctx.send(f"{i.user}: {i.reason}")


def setup(bot):
    bot.add_cog(Achievements(bot))
    bot.add_cog(AchievementCommand(bot))
