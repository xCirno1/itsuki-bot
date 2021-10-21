import discord
import math
import re

from discord.ext import commands
from typing import Dict
from math import sqrt
from operator import pow, truediv, mul, add, sub, is_, is_not

from ext.utils import Calculate, massive_replace
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

    @commands.command(aliases=("qe", "quadratic"))
    async def quadraticequation(self, ctx: Context, *, equation: str):
        """Count some quadratic equation.
        **Example:**
        ```py
        i!qe 5y^2 - 23y - 10 = 0
        or
        i!qe 3X + 12X^2 - 6 = 0
        ```

        __**Note:**__
        1. This only works with 3 **different** group (x^2, x, digit)
        2. You need to simplify the equation, e.g `x + -x^2 + -8` becomes `x -x^2 -8`
        3. This only works with equation resulted 0
        4. Equation without result, the result will be considered as 0
        """
        equation = equation.replace(" ", "")

        def replace_extra_operator(eq):
            to_replace = {
                "+-": "-",
                "--": "+",
                "-+": "-",
                "++": "+"
            }
            return massive_replace(eq, to_replace)
        equation = replace_extra_operator(equation)

        def classify_group(substring: str):
            if "^2" in substring:
                return "A"
            elif substring.isdigit():
                return "C"
            else:
                return "B"

        def parse_quadratic_equation(eq: str):
            if "=" in eq:
                right = eq.split("=")[1]
                if int(right) != 0:
                    raise NotImplementedError("This feature is not implemented yet!")
                eq = eq.split("=")[0]
            if not eq.startswith("-"):
                eq = f"+{eq}"

            order_by: dict = {"A": None, "B": None, "C": None}
            splitted = list(filter(lambda s: ' ' not in s and s, re.split(r"([-+\s])", eq)))
            for c, i in enumerate(splitted):
                if i in ('-', '+'):
                    order_by[classify_group(splitted[c + 1])] = ''.join(i + splitted[c + 1])
            for k, v in order_by.items():
                lc = ''.join([char for count, char in enumerate(v)
                              if (char.isdigit() or char in ("-", "+")) and not v[count - 1] == "^"])
                if lc in ("+", "-"):
                    order_by[k] = int(f'{lc}1')
                else:
                    order_by[k] = int(lc)
            return count_quadratic_equation(order_by)

        def get_discriminant(r):
            if r < 0:
                return "Imaginary"
            elif r == 0:
                return "Twin roots"
            else:
                return "Real and different roots"

        def count_quadratic_equation(ABC: Dict[str, int]):
            a = ABC["A"]
            b = ABC["B"]
            c = ABC["C"]

            d = b ** 2 - 4 * a * c
            try:
                x1 = (-b + sqrt(b ** 2 - 4 * a * c)) / (2 * a)
                x2 = (-b - sqrt(b ** 2 - 4 * a * c)) / (2 * a)
                p = f"""X1,2 = (-b ± √(b^2 - 4ac))/2a
    X1,2 = (-{-b} ± √({b}^2 - 4.{a}.{c}))/2.{a}
    X1,2 = ({f"{-b}" if b < 0 else f"{b}"} ± √({b ** 2} - {4 * a * c}))/{2 * a}
    X1,2 = ({f"{-b}" if b < 0 else f"{b}"} ± √({(b ** 2) - 4 * a * c})/{2 * a}
    X1,2 = ({f"{-b}" if b < 0 else f"{b}"} ± {sqrt((b ** 2) - 4 * a * c)})/{2 * a}

    X1 = ({f"{-b}" if b < 0 else f"{b}"} + {sqrt((b ** 2) - 4 * a * c)})/{2 * a}
    X1 = {(-b if b < 0 else b) + sqrt((b ** 2) - 4 * a * c)}/{2 * a}
    X1 = {((-b if b < 0 else b) + sqrt((b ** 2) - 4 * a * c)) / (2 * a)}

    X2 = ({f"{-b}" if b < 0 else f"{b}"} - {sqrt((b ** 2) - 4 * a * c)})/{2 * a}
    X2 = {(-b if b < 0 else b) - sqrt((b ** 2) - 4 * a * c)}/{2 * a}
    X2 = {((-b if b < 0 else b) - sqrt((b ** 2) - 4 * a * c)) / (2 * a)}
"""
            except ValueError:
                x1 = x2 = "Invalid"
                p = "Math domain error"
            process = f"""
**Datas:**
    A: {a}
    B: {b}
    C: {c}

**Process:**
    {p}

**Discriminant:**
    D = b^2 - 4ac
    D = {b}^2 - (4 * {a} * {c})
    D = {b ** 2} - ({4 * a * c})
    D = {d} ({get_discriminant(d)})
            """
            return f"{x1, x2}", process
        result = parse_quadratic_equation(equation)
        await ctx.send(f"**Answer:** {str(result[0])}\n\n{result[1]}")
        # TODO: add fraction when result is not whole number

def setup(bot):
    bot.add_cog(Math(bot))
