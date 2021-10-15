import discord
import math

from discord.ext import commands
from typing import Dict
from math import sqrt
from operator import pow, truediv, mul, add, sub, is_, is_not

from ext.utils import Calculate
from ext.context import Context


class Math(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=("calc", "c", "math", "count", "solve"))
    async def calculate(self, ctx: Context, *, problem):
        """Calculate some math query.
        Full supported operator:
            '+', '-', '*', 'x', '×', '/', '÷', '^', '**', 'isnot', '==', '!=', 'is''='
        """
        problem = problem.replace(' ', '')
        operators = {
            '+': add,
            '-': sub,
            '*': mul,
            'x': mul,
            '×': mul,
            '/': truediv,
            '÷': truediv,
            '^': pow,
            '**': pow,
            'isnot': is_not,
            '==': is_,
            '!=': is_not,
            'is': is_,
            '=': is_
        }

        def calculate(s):
            if s.isdigit():
                return float(s)
            for c in operators.keys():
                left, operator, right = s.partition(c)
                if operator in operators:
                    return operators[operator](calculate(left), calculate(right))

        await ctx.send(str(calculate(problem)))

    @commands.command()
    async def data(self, ctx, *datas):
        """Find attribute of datas.
        This includes:
            Sorted, Mean, Median, Mode, Range, Quartile-1 (below), Quartile-3 (above), Inter quartile Range
        """
        c = Calculate(list(datas))
        embed = discord.Embed(title="Calculation for your data", color=0xff6666)
        embed.add_field(name="Sorted", value=c.sorted)
        embed.add_field(name="Mean", value=str(c.mean))
        embed.add_field(name="Median", value=str(c.median))
        embed.add_field(name="Mode", value=str(c.mode))
        embed.add_field(name="Range", value=str(c.range))
        embed.add_field(name="Quartile-1", value=str(c.quartil(1)))
        embed.add_field(name="Quartile-3", value=str(c.quartil(3)))
        embed.add_field(name="Inter quartile Range", value=str(c.interquartil_range))
        await ctx.send(embed=embed)

    @commands.command(aliases=("pyth",))
    async def pythagoras(self, ctx: Context, *, sides):
        result = sides.split(',')
        r1, r2 = int(result[0]), int(result[1])
        if r1 > r2:
            answer = math.sqrt(r1 ** 2 - r2 ** 2)
            ways = f"answer:{answer}  " \
                   f"\na^2 + b^2 = c^2  " \
                   f"\na^2 + {r2}^2 = {r1}^2  " \
                   f"\na^2 = {r1 ** 2 - r2 ** 2}" \
                   f"\n**a = {answer}**"
        else:
            answer = math.sqrt(r2 ** 2 - r1 ** 2)
            ways = f"answer:{answer}  " \
                   f"\na^2 + b^2 = c^2  " \
                   f"\na^2 + {r1}^2 = {r2}^2  " \
                   f"\na^2 = {r2 ** 2 - r1 ** 2}" \
                   f"\n**a = {answer}**"
        answer = math.sqrt(r1 ** 2 + r2 ** 2)
        extra = f"answer:{answer}  " \
                f"\na^2 + b^2 = c^2  " \
                f"\n{r1}^2 + {r2}^2 = c^2  " \
                f"\n{r1 ** 2 + r2 ** 2} = c^2" \
                f"\n**c = {answer}**"
        await ctx.send(f"**Find a or b:**"
                       f"\n{ways}\n\n**Find c:**"
                       f"\n{extra}")

    @commands.command()
    async def circle(self, ctx: Context, search):
        """Find a value of either area or perimeter of a circle with given radius. This includes the process too!"""
        embed = discord.Embed(title="Radius value!", description='Input the circle radius!', color=self.bot.base_color)
        await ctx.send(embed=embed)
        r = await self.bot.wait_for("message",
                                    timeout=30,
                                    check=lambda m: m.author == ctx.author and m.channel == ctx.channel
                                    )
        content = int(r.content)
        if search in ("area", "a"):
            base = content ** 2
            if base % 7 != 0:
                answer = base * 3.14
                await ctx.send(
                    f"answer: {answer}"
                    f"\na = π×r^2"
                    f"\na = 3.14×{content}^2"
                    f"\na = 3.14×{base}"
                    f"\n**a = {answer}**")

            elif base % 7 == 0:
                answer = base / 7 * 22
                await ctx.send(
                    f"answer: {answer}"
                    f"\na = π×r^2"
                    f"\na = 22/7×{content}^2"
                    f"\na = 22×{base / 7}"
                    f"\n**a = {answer}**")

        elif search in ("perimeter", "p"):
            if content % 7 != 0:
                answer = content * 6.18
                await ctx.send(
                    f"answer: {answer}"
                    f"\na = 2×π×r"
                    f"\na = 2×3.14×{content}"
                    f"\na = 3.14×{content * 2}"
                    f"\n**a = {answer}**")
            elif content % 7 == 0:
                answer = content * 2 / 7 * 22
                await ctx.send(
                    f"answer: {answer}"
                    f"\na = 2×π×r"
                    f"\na = 2×22/7×{content}"
                    f"\na = 2×22×{content / 7}"
                    f"\na = 22×{content / 7 * 2}"
                    f"\n**a = {answer}**")
        elif search in ("radius", "r"):
            raise NotImplementedError("Feature haven't been implemented and will be implemented soon")
        # TODO: add radius search

    @commands.command()
    async def quadraticequation(self, ctx: Context, *, equation: str):
        def count_quadratic_equation(ABC: Dict[str, int]):
            a = ABC["A"]
            b = ABC["B"]
            c = ABC["C"]
            x1 = (-b + sqrt(b ** 2 - 4 * a * c)) / (2 * a)
            x2 = (-b - sqrt(b ** 2 - 4 * a * c)) / (2 * a)
            return str({x1, x2})

        def parse_quadratic_equation(eq: str):
            chars = [char for count, char in enumerate(eq)
                     if (char.isdigit() or char in ('-', '+')) and eq[count - 1] != "^"]  # split by - or +
            var = 'ABC'
            group_by = {}
            count = 0
            if chars.count('-') + chars.count('+') < 3 and chars[0] in ('-', '+'):
                chars.insert(0, "1")
            if (not chars[0].isdigit() and not chars[1].isdigit()) or chars[0] == "+":
                # prevent bug on equation startswith -X
                chars.insert(0, "1")
            for c, i in enumerate(chars):
                if i.isdigit() and not chars[c - 1].isdigit():  # different group with character before it
                    if var[count] not in group_by:
                        group_by[var[count]] = [chars[c - 1], i]
                    else:
                        group_by[var[count]].append(chars[c - 1])
                        group_by[var[count]].append(i)
                elif i.isdigit() and chars[c - 1].isdigit():  # same group with character before it
                    if var[count] not in group_by:
                        group_by[var[count]] = [i]
                    else:
                        group_by[var[count]].append(i)
                elif (not i.isdigit() and not chars[c - 1].isdigit()) or (not i.isdigit() and c == 0):
                    if var[count] not in group_by:
                        group_by[var[count]] = ["1"]
                    else:
                        group_by[var[count]].append("1")
                if not i.isdigit() and not c == 0:
                    count += 1
            for k, v in group_by.items():
                group_by[k] = int(''.join(v))
            return count_quadratic_equation(group_by)

        result = parse_quadratic_equation(equation)
        await ctx.send(result)


def setup(bot):
    bot.add_cog(Math(bot))
