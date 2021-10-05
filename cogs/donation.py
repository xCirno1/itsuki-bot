# TODO: Add invite listener
import asyncio
import sqlite3
import discord

from typing import Union, Tuple, Any, TYPE_CHECKING, List, Optional, TypeVar
from datetime import datetime
from discord.ext import commands, tasks
from enums import Members, Channels, ClanOwners
from ext.decorators import check_access
from ext.context import Context
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


class DonationCog(commands.Cog, name="Clan Donation"):
    def __init__(self, bot):
        self.bot = bot
        self.db = sqlite3.connect("donation.db")
        self.cur = self.db.cursor()
        self.refresh_daily.start()

    @commands.command(aliases=("remove",))
    @check_access(ClanOwners)
    async def kick(self, ctx: Context, member: discord.Member, *, reason: str = "No reason provided."):
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
        try:
            await self.bot.wait_until_ready()
            print(datetime.utcnow())
            if datetime.utcnow().strftime("%H:%M") == "00:00":
                self.cur.execute("SELECT acc_id FROM data")
                ti: List[Tuple[int, ...]] = self.cur.fetchall()
                ids: List[int, ...] = [t[0] for t in ti]
                for d in ids:
                    cls: DonationData = DonationData(d)
                    donation_today = cls.select("donation_today")
                    if donation_today < MINIMUM_DONATION:  # implement debt
                        cls.add("debt", MINIMUM_DONATION - donation_today)  # count the difference

                    elif donation_today > MINIMUM_DONATION:  # implement debt cover
                        if cls.select("debt") > 0:
                            cls.add("debt", -(donation_today - MINIMUM_DONATION))

                    if donation_today == 0:  # did not donate
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
        except Exception as e:
            with open("debug.txt", "a") as f:
                f.write('\n' + str(e) + '\n')
            raise e

    @commands.command()
    async def invite(self, ctx: Context, member: Union[T, List[T]]) -> Optional[discord.Message]:
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
        self.db.commit()
        await ctx.send(f"Added {member} to database!")

    @commands.command(aliases=("di", "dinfo", "donation_info"))
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
