class EnumMeta(type):
    """This metaclass makes a class iterable (iterate through class vars)."""
    def __new__(mcs, name, sub, attrs, *args, **kwargs):
        attrs["type"] = kwargs.get('type')
        attrs["abc"] = kwargs.get('abc', False)
        return super().__new__(mcs, name, sub, attrs)

    def __iter__(self):
        yield from [i for i in self.__dict__.values() if str(i).isdigit()]


class Channels(metaclass=EnumMeta, type="GuildChannel", abc=True):
    promote    = 798095614759403530
    level_up   = 786820544493518878
    donation   = 832062465692663838
    bot_test   = 810304486341738527
    suggestion = 786608266208608336


class Members(metaclass=EnumMeta, type="Member"):
    disboard = 302050872383242240
    arcane   = 437808476106784770
    anigame  = 571027211407196161


class ClanOwners(metaclass=EnumMeta, type="Member"):
    yuki  = 685763623221854258
    kylee = 650447110402998302
    jack  = 369144046284701696


class Roles(metaclass=EnumMeta, type="Role"):
    clan_members = 832104392907554868
