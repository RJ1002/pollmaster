import discord

from essentials.secrets import SECRETS


class Settings:
    def __init__(self):
        self.color = discord.Colour(int('e75e28', 16))
        self.title_icon = "https://i.imgur.com/MvJIuB7.jpg" #PM
        self.author_icon = "https://i.imgur.com/zqHvRvz.jpg" #tag
        self.report_icon = "https://i.imgur.com/YDBQm3U.png" #report
        self.owner_id = 183940132129210369
        self.msg_errors = False #send a DM to bot owner about a error(make sure you edit self.owner_id so the bot know who the bot owner is)
        self.log_errors = True
        self.invite_link = \
            'https://discord.com/oauth2/authorize?client_id=753217458029985852&permissions=275951774784&scope=bot%20applications.commands'

        self.load_secrets()

    def load_secrets(self):
        # secret
        self.dbl_token = SECRETS.dbl_token
        self.mongo_db = SECRETS.mongo_db
        self.bot_token = SECRETS.bot_token
        self.mode = SECRETS.mode


SETTINGS = Settings()
