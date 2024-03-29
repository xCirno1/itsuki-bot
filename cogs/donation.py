# TODO: Add invite listener
import asyncio
import discord
import sqlite3
import time

from argparse import ArgumentParser
from datetime import datetime
from discord.ext import commands, tasks
from typing import Union, Tuple, Any, TYPE_CHECKING, List, Optional, TypeVar, Literal

from enums import Members, Channels, ClanOwners, HistoryType
from ext.context import Context
from ext.decorators import check_access
from ext.pagination import Paginate
from ext.utils import ignore

if TYPE_CHECKING:
    from sqlite3 import Connection, Cursor

db: "Connection" = sqlite3.connect("donation.db", timeout=10)
cur: "Cursor" = db.cursor()
T = TypeVar("T", bound=discord.Member)
ignore("CREATE TABLE IF NOT EXISTS data(id INTEGER PRIMARY KEY AUTOINCREMENT, "
       "acc_id INT, times_donated INT, donation_value INT, donation_streak INT, "
       "donation_today INT, joined_at TEXT, not_donate_days INT, debt INT)")
ignore("CREATE TABLE IF NOT EXISTS kicked(id INTEGER PRIMARY KEY AUTOINCREMENT, "
       "acc_id INT, reason TEXT, date TEXT)")
ignore("CREATE TABLE IF NOT EXISTS history(id INTEGER PRIMARY KEY AUTOINCREMENT, "
       "acc_id INT, action TEXT, timestamp INT, type TEXT)")

MINIMUM_DONATION: int = 20000


class DonationData:
    def __init__(self, _id: int):
        self.cur: Cursor = cur
        self.db: Connection = db
        self.id: int = _id
        self.joined_at: str = self.select("joined_at")  # should be datetime.datetime, but sqlite doesn't support it
        self.key: int = self.select("id")
        self.acc_id: int = self.select("acc_id")  # not really needed but to complete everything

    @property
    def total_donation(self) -> int:
        return self.select("donation_value")

    @property
    def not_donate_days(self) -> int:
        return self.select("not_donate_days")

    @property
    def debt(self) -> int:
        return self.select("debt")

    @property
    def donation_streak(self) -> int:
        return self.select("donation_streak")

    @property
    def donation_today(self) -> int:
        return self.select("donation_today")

    @property
    def times_donated(self) -> int:
        return self.select("times_donated")

    def add(self, col: str, by: int) -> int:
        """Add a user to database."""
        self.cur.execute(f"SELECT {col} FROM data WHERE acc_id = ?", (self.id,))
        res: int = int(cur.fetchone()[0])
        self.cur.execute(f"UPDATE data SET {col}=? WHERE acc_id = ?", (res + by, self.id))
        self.db.commit()
        return self.select(col)

    def set(self, col: str, to: Union[int, str]) -> Any:
        """Set a selected column with a given id to a given value."""
        self.cur.execute(f"UPDATE data SET {col}=? WHERE acc_id = ?", (to, self.id))
        self.try_commit()
        return self.select(col)

    def select(self, col: str) -> Any:
        """Returns a selected column by given id."""
        self.cur.execute(f"SELECT {col} FROM data WHERE acc_id=?", (self.id,))
        return self.cur.fetchone()[0]

    def delete(self) -> None:
        """Delete a row by given id."""
        self.cur.execute("DELETE FROM data WHERE acc_id=?", (self.id,))
        self.try_commit()

    def try_commit(self) -> None:
        try:
            self.db.commit()
        except sqlite3.OperationalError:
            pass


class History:
    def __init__(self, _id):
        self.id = _id
        self.cur: Cursor = cur
        self.db: Connection = db
        self.key = self.select("id")
        self.acc_id = self.select("acc_id")

    def fetch_history(self, timestamp: int = None, from_date: int = None, from_type: str = None):
        if timestamp is not None and from_date is not None:
            raise NotImplementedError
        if timestamp is None and from_date is None and from_type is None:
            return self.select("action", fetch_all=True)
        elif timestamp is not None and from_type is None:
            return self.select("action", fetch_all=False, extra_condition=f"AND timestamp = {timestamp}")
        elif from_date is not None and from_type is None:
            return self.select("action", fetch_all=True, extra_condition=f"AND timestamp > {timestamp}")
        elif timestamp is not None and from_type is not None:
            return self.select("action",
                               fetch_all=False,
                               extra_condition=f"AND timestamp = {timestamp} AND type = {from_type}")
        elif from_date is not None and from_type is not None:
            return self.select("action",
                               fetch_all=True,
                               extra_condition=f"AND timestamp > {timestamp} AND type = {from_type}")

    def select(self, *col: str, fetch_all: bool = False,
               extra_condition: str = "",
               order_by: Literal["desc", "asc"] = "asc",
               order_by_param: str = "timestamp") -> Any:
        """Returns a selected column by given id."""
        self.cur.execute(f"SELECT {', '.join(col)} FROM history WHERE "
                         f"acc_id=? {extra_condition if extra_condition else ''} "
                         f"ORDER BY {order_by_param} {order_by}", (self.id,))
        if fetch_all:
            return self.cur.fetchall()
        return self.cur.fetchone()[0]

    def add_history(self, action: str, timestamp: int, _type: str):
        self.cur.execute("INSERT INTO history (acc_id, action, timestamp, type) VALUES (?, ?, ?, ?)",
                         (self.acc_id, action, timestamp, _type))
        self.db.commit()


class DonationCog(commands.Cog, name="Clan Donation"):
    def __init__(self, bot):
        self.bot = bot
        self.db = sqlite3.connect("donation.db")
        self.cur = self.db.cursor()
        self.refresh_daily.start()

    @commands.command(aliases=("remove",))
    @check_access(ClanOwners)
    async def clankick(self, ctx: Context, member: discord.Member, *, reason: str = "No reason provided."):
        """Remove a user from clan database."""
        m = await ctx.send(f"Are you sure you want to kick {member.display_name} from clan?\n\nReason: {reason}")
        if await ctx.send_confirmation(message=m, timeout=60):
            self.cur.execute("INSERT INTO kicked (acc_id, reason, date) VALUES (?, ?, ?)",
                             (member.id, reason, datetime.now().strftime("%a, %d %b %y %H:%M")))
            self.db.commit()

            await ctx.send("Processing...")
            await asyncio.sleep(3)
            d = DonationData(member.id)
            d.delete()
            await ctx.send(f"Removed {member} from database!")
        else:
            await m.clear_reactions()

    @tasks.loop(minutes=1)
    async def refresh_daily(self):
        """This will be the process of daily donation checking and reset."""
        # currently implemented: debt, not_donate_days, donation_today, donation_streak
        await self.bot.wait_until_ready()
        if datetime.utcnow().strftime("%H:%M") == "04:56":
            self.cur.execute("SELECT acc_id FROM data")
            ti: List[Tuple[int, ...]] = self.cur.fetchall()
            ids: List[int, ...] = [t[0] for t in ti]
            for d in ids:
                hcls: History = History(d)
                cls: DonationData = DonationData(d)
                hcls.add_history(f"Daily reset: Donated {cls.select('donation_today')} gold today",
                                 int(time.time()), HistoryType.reset)
                donation_today = cls.select("donation_today")
                if donation_today < MINIMUM_DONATION:  # implement debt
                    cls.add("debt", MINIMUM_DONATION - donation_today)  # count the difference
                elif donation_today > MINIMUM_DONATION:  # implement debt cover
                    if cls.select("debt") > 0:
                        if -(donation_today - MINIMUM_DONATION) < 0:
                            cls.add("debt", 0)
                        else:
                            cls.add("debt", -(donation_today - MINIMUM_DONATION))

                if donation_today == 0:  # did not donate
                    if (streak := cls.select("donation_streak")) > 0:
                        hcls.add_history(f"Streak lost: {streak} streaks",
                                         timestamp=int(time.time()),
                                         _type=HistoryType.streak_lost)
                    cls.add("not_donate_days", 1)
                    cls.set("donation_streak", 0)
                    user: discord.User = self.bot.get_user(d)
                    base_message: str = f"Hi, it seems you haven't donated for {cls.not_donate_days} days."
                    if cls.not_donate_days == 2:  # did not donate 2 days
                        await user.send(f"{base_message}!\n_4 days is the maximum days you don't donate._")
                    elif cls.not_donate_days == 3:
                        await user.send(f"{base_message}!\n__**1 days left until the maximum days!**__")
                    elif cls.not_donate_days == 4:
                        await user.send(f"{base_message}!\nI have informed our clan leaders!")
                        channel: discord.TextChannel = self.bot.get_channel(Channels.bot_test)
                        await channel.send(f"{d}, did not donate for 4 days!")
                    elif cls.not_donate_days > 4:
                        channel: discord.TextChannel = self.bot.get_channel(Channels.bot_test)
                        await channel.send(f"{d}, did not donate for {cls.not_donate_days} days!")

                else:  # donate, reset the not_donate_days
                    cls.set("not_donate_days", 0)
                    cls.add("donation_streak", 1)
                cls.set("donation_today", 0)

    @commands.command()
    async def invite(self, ctx: Context, member: discord.Member) -> Optional[discord.Message]:
        """Invite a user to be added to database."""
        self.cur.execute("SELECT acc_id FROM data WHERE acc_id = ?", (member.id,))
        res: Tuple[Optional[int]] = self.cur.fetchone()
        try:
            if member.id in res:
                return await ctx.send("It seems that this member exists already in database!")
        except TypeError:
            pass
        self.cur.execute("INSERT INTO data (acc_id, times_donated, donation_value, donation_streak, "
                         "donation_today, joined_at, not_donate_days, debt) VALUES (?, 0, 0, 0, 0, ?, 0, 0)",
                         (member.id, datetime.now().strftime("%a, %d %b %y %H:%M")))
        self.cur.execute("INSERT INTO history (acc_id, action, timestamp, type) VALUES (?, ?, ?, ?)",
                         (member.id, f"Clan invite by: {ctx.author.name} ({ctx.author.id})",
                          time.time(), HistoryType.clan_invite))
        self.db.commit()
        await ctx.send(f"Added {member} to database!")

    @commands.group(aliases=("di", "dinfo", "donation_info"), invoke_without_command=True)
    async def donationinfo(self, ctx: Context, member: discord.Member = None) -> None:
        """Shows a description of a member. Defaulted to message's author."""
        member: discord.Member = member or ctx.author
        cls: DonationData = DonationData(member.id)
        embed = discord.Embed(title=f"Showing Information for {member}!",
                              description=f"\n**Times donated:** {cls.times_donated} times"
                                          f"\n**Total donation:** {cls.total_donation}"
                                          f"\n**Streak:** {cls.donation_streak}"
                                          f"\n**Debt:** {cls.debt}"
                                          f"\n**Donation today:** {cls.donation_today}"
                                          f"\n\n_Found a bug? Report it at <#{Channels.suggestion}>._",
                                          color=self.bot.base_color
                              ).set_footer(text=f"Joined at: {cls.joined_at}", icon_url=member.avatar_url)
        await ctx.reply(embed=embed)

    @donationinfo.command()
    async def history(self, ctx: Context, member: Optional[discord.Member] = None,
                      *, flags: str = ""):
        """Display anigame action history.
        This includes:
        - Clan join
        - Clan donate
        - Daily refresh

        **Available flags:**
        `-sort`: Sort the query by *asc* (ascending) or *desc* descending
        `-in`: Display the query **by** a specific unix timestamp
        `-from`: Display the query **from** a specific unix timestamp
        `-action`: Display the query by a specific action ("donation", "invite", "kick", "warning",
        "upgrade", "streak_lost", "reset")
        """
        parser = ArgumentParser(add_help=False, allow_abbrev=False)
        parser.add_argument('-sort')
        parser.add_argument('-in', dest='in_')
        parser.add_argument('-from', dest='from_')
        parser.add_argument('-action')
        args = parser.parse_args(flags.split())
        member = member or ctx.author
        cls = History(member.id)
        action = f"AND type='{args.action}'" if args.action else ""
        _from = f"AND {args.from_}" if args.from_ else ""
        res = cls.select("action", "timestamp",
                         extra_condition=(f"AND timestamp = {args.in_}"
                                          if args.in_ else _from) + action,
                         fetch_all=True, order_by=args.sort if args.sort else "desc", order_by_param="timestamp")
        embed = discord.Embed(title=f"Viewing {member.name}'s history", description="", color=self.bot.base_color)
        string = ""
        for count, data in enumerate(res, 1):
            string += f"{count}. {data[0]} | <t:{int(data[1])}:R>\n"
        pag = Paginate
        pag.from_context(ctx)
        pag(pages=[embed]).auto_paginate(string=string)

    @commands.Cog.listener("on_message")
    async def donation_listener(self, message: discord.Message) -> None:
        if (message.content.startswith(".cl donate") or message.content.startswith(".clan donate")) \
                and message.channel.id in (Channels.donation,):
            try:
                await self.bot.wait_for("message", check=lambda m: m.author.id == Members.anigame and m.embeds[
                    0].title.lower().startswith("success"), timeout=4)  # to handle Anigame's latency

                # implement invite if user not in database
                self.cur.execute("SELECT acc_id FROM data WHERE acc_id=?", (message.author.id,))
                if not self.cur.fetchone():
                    await ((await self.bot.get_context(message)).invoke(self.bot.get_command("invite"), message.author))
                # extract the first group of ints
                val = int([w for w in message.content.split() if w.isdigit()][0])
                # all data will be moved to tasks.loop except: times_donated, donation_today, donation_value,
                # donation_streak
                cls = DonationData(message.author.id)
                dv: int = cls.add("donation_value", val)
                cls.add("times_donated", 1)
                dt: int = cls.add("donation_today", val)

                # Add to history
                hcls = History(message.author.id)
                hcls.add_history(f"Donated: {val} gold", timestamp=int(time.time()), _type=HistoryType.donation)

                base_title = "Thanks for donating"
                base_description = f"You have donated {dt} gold today and a total of {dv} gold!"
                base_footer = f"To view your donation details type `i!dinfo`."

                if dt > MINIMUM_DONATION:
                    base_title += f" more than {MINIMUM_DONATION}!"
                else:
                    base_title += "!"

                embed = discord.Embed(title=base_title, description=base_description, color=self.bot.base_color)
                embed.set_footer(text=base_footer)
                try:
                    await message.author.send(embed=embed)
                except (discord.Forbidden, discord.HTTPException):
                    reply: discord.Message = await message.reply(content="Unable to send dm but don't worry,"
                                                                         " your data is saved!")
                    await asyncio.sleep(10)
                    await reply.delete()
            except asyncio.TimeoutError:
                await message.channel.send("Unable to save data! This is probably due "
                                           "to high latency or no response anigame's end.")


def setup(bot):
    bot.add_cog(DonationCog(bot))
