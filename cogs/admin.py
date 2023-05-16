import logging

import discord
from discord.ext import commands
from discord import app_commands

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # every commands needs owner permissions
    async def cog_check(self, ctx):
        return self.bot.owner == ctx.author.id

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.reply("Only the owner can use this module. Join the support discord server if you are having "
                           f"any problems. This usage has been logged.")
            logger.warning(f'User {ctx.author} ({ctx.author.id}) has tried to access a restricted '
                           f'command via {ctx.message.content}.')
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("Missing a required argument for this command.")
        else:
            logger.warning(error)

    @commands.hybrid_command(aliases=['r'], description="Reloads cogs")
    @app_commands.describe(
        cog='options: config, poll_controls, help, db_api, admin',
    )
    async def reload(self, ctx, *, cog):
        if cog == 'c':
            cog = 'poll_controls'

        logger.info(f'Trying to reload cog: cogs.{cog}.')

        reply = ''
        try:
            await self.bot.reload_extension('cogs.'+cog)
            reply = f'Extension "cogs.{cog}" successfully reloaded.'
        except commands.ExtensionNotFound:
            reply = f'Extension "cogs.{cog}" not found.'
        except commands.NoEntryPointError:
            reply = f'Extension "cogs.{cog}" is missing a setup function.'
        except commands.ExtensionFailed:
            reply = f'Extension "cogs.{cog}" failed to start.'
        except commands.ExtensionNotLoaded:
            reply = f'Extension "cogs.{cog}" is not loaded... trying to load it. '
            try:
                await self.bot.load_extension('cogs.'+cog)
            except commands.ExtensionAlreadyLoaded:
                reply += f'Could not load or reload extension since it is already loaded...'
            except commands.ExtensionNotFound:
                reply += f'Extension "cogs.{cog}" not found.'
            except commands.ExtensionFailed:
                reply = f'Extension "cogs.{cog}" failed to start.'
        finally:
            logger.info(reply)
            await ctx.reply(reply)
            
    id = str
    @app_commands.command(name="guildleave", description="make bot leave a specified guild")
    async def guildleave(self, ctx, *, id: id = None):
        result = await self.bot.db.config.find_one({'_id': id})
        if not isinstance(ctx.channel, discord.TextChannel):
            await ctx.response.send_message("`/guildleave` can only be used in a server text channel.", delete_after=60)
            return
        guild = ctx.guild
        if not guild:
            await ctx.response.send_message("Could not determine your server. Run the command in a server text channel.", delete_after=60)
            return
        if not self.bot.owner == ctx.user.id:
            await ctx.response.send_message("Only the owner can use this module. Join the support discord server if you are having "
                           f"any problems. This usage has been logged.", delete_after=60)
            logger.warning(f'User {ctx.user} ({ctx.user.id}) has tried to access a restricted '
                           f'command via /guildleave.')
            return
        if not id:
            await ctx.response.send_message(f'you need to choose a guild id! ', delete_after=60)
            return
        if not result:
            await ctx.response.send_message(f'guild id `{id}` not found.', delete_after=60)
            return
        if id == result.get('_id'):
              guildobject = self.bot.get_guild(int(id))
              await ctx.response.send_message(f'bot left {id} {guildobject}', delete_after=60)
              await guildobject.leave()
              return
        else:
            await ctx.response.send_message(f'guild id `{id}` not found.', delete_after=60)


async def setup(bot):
    global logger
    logger = logging.getLogger('discord')
    await bot.add_cog(Admin(bot))
