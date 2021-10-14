from discord.ext.commands import CheckFailure


class NotAllowed(CheckFailure):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
