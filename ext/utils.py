import discord

from typing import Union, Callable, List, Dict


class Converter:
    @staticmethod
    def audit_log_action(_from: str) -> discord.AuditLogAction:
        """Convert a string to an AuditLogAction class."""
        if _from.startswith("on_"):
            _from = _from[2:]
        attr = getattr(discord.AuditLogAction, _from, None)
        return attr


def romanize(_from: int) -> str:
    """Returns a roman number version from the given int"""
    val = [
        1000, 900, 500, 400,
        100, 90, 50, 40,
        10, 9, 5, 4,
        1
    ]
    syb = [
        "M", "CM", "D", "CD",
        "C", "XC", "L", "XL",
        "X", "IX", "V", "IV",
        "I"
    ]
    roman_num = ''
    i = 0
    while _from > 0:
        for _ in range(_from // val[i]):
            roman_num += syb[i]
            _from -= val[i]
        i += 1
    return roman_num


def remove(query: str, removable: Union[str, list]) -> str:
    """
    Removes a part of string of a string.
    """
    a = ""
    if removable not in query and not isinstance(removable, list):
        return query
    else:
        if isinstance(removable, list):
            for elem in removable:
                a + query.replace(elem, "")
        else:
            a + query.replace(removable, "")
    return a


def is_dunder(obj: Union[str, Callable, object, type], _assert: bool = False) -> bool:
    """Check if an object is a dunder method, assertion is applicable here too."""
    stmt = obj.startswith("__") and obj.endswith("__")
    if _assert:
        assert stmt
    return stmt


def ignore(*args, **kwargs) -> None:
    """Do nothing."""
    pass


def massive_replace(_str: str, _dict: Dict[str, str]) -> str:
    for k, v in _dict.items():
        _str = _str.replace(k, v)
    return _str


def replace_not_digit(data: str) -> List[int]:
    a = []
    b = []
    for e in data:
        if e.isdigit():
            a.append(e)
        else:
            try:
                b.append(int(''.join(a)))
                a = []
            except ValueError:
                pass
    else:
        b.append(int(''.join(a)))
    return b


class Calculate:
    def __init__(self, data: Union[str, List[Union[str, int]]]):
        if not isinstance(data, List):
            self.data = replace_not_digit(data)
        else:
            self.data = [int(e) for e in data]
        self.sorted = sorted(self.data)

    @property
    def mean(self) -> float:
        return round(sum(int(s) for s in self.data)/len(self.data), 3)

    @property
    def median(self) -> Union[float, int]:
        sorted_data = sorted(self.data)
        index = (len(sorted_data) + 1)//2

        if len(sorted_data) % 2 == 0:
            return (int(sorted_data[index - 1]) + int(sorted_data[index]))/2
        return sorted_data[index - 1]

    @property
    def mode(self) -> int:
        diff = set(self.data)
        count = {}
        for d in diff:
            count[d] = 0
        return max(set(self.data), key=self.data.count)

    def quartil(self, n: int) -> Union[float, int]:
        sorted_data = sorted(self.data)
        if len(sorted_data) % 2 == 1:  # jumlah data ganjil
            new = (sorted_data[:(len(sorted_data))//2] if n == 1 else sorted_data[(len(sorted_data) + 1)//2:])
        else:  # jumlah data genap
            new = sorted_data[:((len(sorted_data) + 1) // 2)] if n == 1 else sorted_data[((len(sorted_data) + 1)//2):]
        index = (len(new) + 1)//2
        if len(new) % 2 == 0:
            return (int(new[index - 1]) + int(new[index - 0])) / 2

        return new[index - 1]

    @property
    def range(self) -> int:
        return max(self.data) - min(self.data)

    @property
    def interquartil_range(self) -> Union[float, int]:
        return self.quartil(3) - self.quartil(1)
