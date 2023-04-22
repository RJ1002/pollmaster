import discord

from essentials.secrets import SECRETS


class Settings:
    def __init__(self):
        self.color = discord.Colour(int('e75e28', 16))
        self.title_icon = "https://i.imgur.com/0T8QJXT.jpg" #PM
        self.author_icon = "https://i.imgur.com/BxtNIab.jpg" #tag
        self.report_icon = "https://i.imgur.com/GVVDZ31.png" #report
        self.owner_id = 183940132129210369
        self.msg_errors = True
        self.log_errors = True
        self.invite_link = \
            'https://discord.com/api/oauth2/authorize?client_id=687418918658375695&permissions=1073867840&scope=bot'

        self.load_secrets()

    def load_secrets(self):
        # secret
        self.dbl_token = SECRETS.dbl_token
        self.mongo_db = SECRETS.mongo_db
        self.bot_token = SECRETS.bot_token
        self.mode = SECRETS.mode


SETTINGS = Settings()
