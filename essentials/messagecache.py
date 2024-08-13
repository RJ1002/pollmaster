import logging
import discord

logger = logging.getLogger('discord')


class MessageCache:
    def __init__(self, bot):
        self.bot = bot
        self._cache_dict = {}

    def put(self, key, value: discord.Message):
        self._cache_dict[key] = value
        if self._cache_dict.__len__() % 5 == 0:
            logger.info("cache size: " + str(self._cache_dict.__len__()))

    def get(self, key):
        # Try to find it in this cache, then see if it is cached in the bots own message cache
        message = self._cache_dict.get(key, None)
        return message

    def clear(self):
        self._cache_dict = {}