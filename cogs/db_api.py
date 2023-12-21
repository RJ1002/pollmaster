import logging
import topgg

from discord.ext import tasks, commands

from essentials.settings import SETTINGS


class DiscordBotsOrgAPI(commands.Cog):
    """Handles interactions with the discordbots.org API"""

    def __init__(self, bot):
        self.bot = bot
        if SETTINGS.mode != "development":
            self.token = SETTINGS.dbl_token
            self.topggpy = topgg.DBLClient(self.bot, self.token, autopost=True, post_shard_count=True)
            self.update_stats.start()

    def cog_unload(self):
        self.update_stats.cancel()

    @commands.Cog.listener()
    async def on_autopost_success(self):
        logger.info(f'Posted server count: ({self.topggpy.guild_count}), shard count: ({self.bot.shard_count})')
    
    @commands.Cog.listener()
    async def on_autopost_error(exception):
        logger.exception('Failed to post server count\n{}: {}'.format(type(exception).__name__, exception))

    #@tasks.loop(minutes=30.0)
    #async def update_stats(self):
    #    """This function runs every 30 minutes to automatically update your server count"""
    #    logger.info('Attempting to post server count')
    #    try:
    #        await self.dblpy.post_guild_count()
    #        logger.info('Posted server count ({})'.format(self.dblpy.guild_count()))
    #        sum_users = 0
    #        for guild in self.bot.guilds:
    #            sum_users += len(guild.members)
    #        logger.info(f'total users served by the bot: {sum_users}')
    #    except Exception as e:
    #        logger.exception('Failed to post server count\n{}: {}'.format(type(e).__name__, e))


async def setup(bot):
    global logger
    logger = logging.getLogger('discord')
    await bot.add_cog(DiscordBotsOrgAPI(bot))
