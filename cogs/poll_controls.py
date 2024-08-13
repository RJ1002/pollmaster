import traceback
import argparse
import datetime
import logging
import random
import shlex
import time
from string import ascii_lowercase
import regex

import discord
from discord.ui import Button, View, Modal, TextInput
import pytz
from bson import ObjectId
from discord.ext import tasks, commands

from discord import app_commands
from essentials.exceptions import StopWizard
from essentials.multi_server import get_server_pre, ask_for_server, ask_for_channel
from essentials.settings import SETTINGS
from models.poll import Poll
from utils.misc import CustomFormatter
from utils.paginator import embed_list_paginated
from utils.poll_name_generator import generate_word

# A-Z Emojis for Discord
AZ_EMOJIS = [(b'\\U0001f1a'.replace(b'a', bytes(hex(224 + (6 + i))[2:], "utf-8"))).decode("unicode-escape") for i in
             range(26)]


class PollControls(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ignore_next_removed_reaction = {}
        self.index = 0
        self.close_activate_polls.add_exception_type(KeyError)
        self.close_activate_polls.start()
        self.refresh_queue.start()

    def cog_unload(self):
        self.close_activate_polls.cancel()
        self.refresh_queue.cancel()

    # noinspection PyCallingNonCallable
    @tasks.loop(seconds=30)
    async def close_activate_polls(self):
        if hasattr(self.bot, 'db') and hasattr(self.bot.db, 'polls'):
            utc_now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)

            # auto-close polls
            query = self.bot.db.polls.find({'open': True, 'duration': {
                '$gte': utc_now - datetime.timedelta(weeks=8),
                '$lte': utc_now + datetime.timedelta(minutes=1)
            }})
            if query:
                for limit, pd in enumerate([poll async for poll in query]):
                    if limit >= 30:
                        print("More than 30 polls due to be closed! Throttling to 30 per 30 sec.")
                        logger.warning("More than 30 polls due to be closed! Throttling to 30 per 30 sec.")
                        break

                    # load poll (this will close the poll if necessary and update the DB)
                    p = Poll(self.bot, load=True)
                    if not p:
                        continue
                    await p.from_dict(pd)

                    # Check if Pollmaster is still present on the server
                    if not p.server:
                        # Bot is not present on that server. Close poll directly in the DB.
                        await self.bot.db.polls.update_one({'_id': p.id}, {'$set': {'open': False}})
                        logger.info(f"Closed poll on a server ({pd['server_id']}) without Pollmaster being present.")
                        continue
                    # Check if poll was closed and inform the sever if the poll is less than 2 hours past due
                    # (Closing old polls should only happen if the bot was offline for an extended period)
                    if not p.open:
                        if p.duration.replace(tzinfo=pytz.utc) >= utc_now - datetime.timedelta(hours=2):
                            # only send messages for polls that were supposed to expire in the past 2 hours
                            try:
                                guild_config = await self.bot.db.config.find_one({'_id': str(p.server.id)},{'_id': 1, 'error_mess': 2, 'closedpoll_mess': 3 })
                                if guild_config and not guild_config.get('closedpoll_mess') or guild_config and guild_config.get('closedpoll_mess') == 'True':
                                    await p.channel.send('This poll has reached the deadline and is closed!')
                                    await p.post_embed(p.channel)
                                else:
                                    print('will not send message for closed poll!!', guild_config)
                                #await p.channel.send('This poll has reached the deadline and is closed!')
                                #await p.post_embed(p.channel)
                            except:
                                logger.warning(f"Failed to send message for a closed poll: {p.server.id}")
                                # send bot owner a DM
                                warningdm = await self.bot.fetch_user(self.bot.owner)
                                e = discord.Embed(
                                    title=f"Error With: Failed to send message for a closed poll",
                                    description=f"```py\n{type(self).__name__}: {traceback.format_exc(limit=0)}\n```\n\nContent: {p.short}"
                                                f"\n\tServer: {p.server}\n\tServerid: {p.server.id}\n\tChannel: #{f'{p.channel.id}' if p.channel is not None else 'None'}",
                                    timestamp=None
                                )
                                await warningdm.send(embed=e)
                        else:
                            logger.info(f"Closing old poll: {p.id}")

            # auto-activate polls
            query = self.bot.db.polls.find({'active': False, 'activation': {
                '$gte': utc_now - datetime.timedelta(weeks=8),
                '$lte': utc_now + datetime.timedelta(minutes=1)
            }})
            if query:
                for limit, pd in enumerate([poll async for poll in query]):
                    if limit >= 10:
                        print("More than 10 polls due to be closed! Throttling to 10 per 30 sec.")
                        logger.warning("More than 10 polls due to be closed! Throttling to 10 per 30 sec.")
                        break

                    # load poll (this will activate the poll if necessary and update the DB)
                    p = Poll(self.bot, load=True)
                    await p.from_dict(pd)

                    # Check if Pollmaster is still present on the server
                    if not p.server:
                        # Bot is not present on that server. Close poll directly in the DB.
                        await self.bot.db.polls.update_one({'_id': p.id}, {'$set': {'active': True}})
                        logger.info(f"Activated poll on a server ({pd['server_id']}) without Pollmaster being present.")
                        continue
                    # Check if poll was activated and inform the sever if the poll is less than 2 hours past due
                    # (activating old polls should only happen if the bot was offline for an extended period)
                    if p.active:
                        if p.activation.replace(tzinfo=pytz.utc) >= utc_now - datetime.timedelta(hours=2):
                            # only send messages for polls that were supposed to expire in the past 2 hours
                            try:
                                await p.channel.send('This poll has been scheduled and is active now!')
                                await p.post_embed(p.channel)
                            except:
                                logger.warning(f"Failed to send message for a active poll: {p.server.id}")
                                # send bot owner a DM
                                warningdm = await self.bot.fetch_user(self.bot.owner)
                                e = discord.Embed(
                                    title=f"Error With: Failed to send message for a active poll",
                                    description=f"```py\n{type(self).__name__}: {traceback.format_exc(limit=0)}\n```\n\nContent: {p.short}"
                                                f"\n\tServer: {p.server}\n\tServerid: {p.server.id}\n\tChannel: #{p.channel.id}",
                                    timestamp=None
                                )
                                await warningdm.send(embed=e)
                        else:
                            logger.info(f"Activating old poll: {p.id}")
        else:
            print('unknown error for close_activate_polls')
            logger.info(f"unknown error for close_activate_polls")

    @close_activate_polls.before_loop
    async def before_close_activate_polls(self):
        # print('close task waiting...')
        await self.bot.wait_until_ready()

    @tasks.loop(seconds=5)
    async def refresh_queue(self):
        remove_list = []
        for pid, t in self.bot.refresh_blocked.items():
            if t - time.time() < 0:
                remove_list.append(pid)
                if self.bot.refresh_queue.get(pid, False):
                    query = await self.bot.db.polls.find_one({'_id': ObjectId(pid)})
                    if query:
                        p = Poll(self.bot, load=True)
                        if p:
                            await p.from_dict(query)
                            await p.refresh(self.bot.refresh_queue.get(pid))
                            del self.bot.refresh_queue[pid]

        # don't change dict while iterating
        for pid in remove_list:
            del self.bot.refresh_blocked[pid]

    @refresh_queue.before_loop
    async def before_refresh_queue(self):
        # print('refresh task waiting...')
        await self.bot.wait_until_ready()

    # General Methods
    @staticmethod
    def get_label(message: discord.Message):
        label = None
        if message and message.embeds:
            embed = message.embeds[0]
            label_object = embed.author
            if label_object:
                label_full = label_object.name
                if label_full and label_full.startswith('>> '):
                    label = label_full[3:]
        return label

    async def is_admin_or_creator(self, ctx, server, owner_id, error_msg=None):
        member = ctx.user
        # member = server.get_member(ctx.message.author.id)
        if member.id == owner_id:
            return True
        elif member.guild_permissions.manage_guild:
            return True
        else:
            result = await self.bot.db.config.find_one({'_id': str(server.id)})
            if result and result.get('admin_role') in [r.name for r in member.roles]:
                return True
            else:
                if error_msg is not None:
                    await ctx.user.send(error_msg)
                return False

    async def say_error(self, ctx, error_text, footer_text=None):
        embed = discord.Embed(title='', description=error_text, colour=SETTINGS.color)
        embed.set_author(name='Error', icon_url=SETTINGS.author_icon)
        if footer_text is not None:
            embed.set_footer(text=footer_text)
        await ctx.followup.send(embed=embed)

    async def say_embed(self, ctx, say_text='', title='RT Pollmaster', footer_text=None):
        embed = discord.Embed(title='', description=say_text, colour=SETTINGS.color)
        embed.set_author(name=title, icon_url=SETTINGS.author_icon)
        if footer_text is not None:
            embed.set_footer(text=footer_text)
        await ctx.followup.send(embed=embed)

    # Commands
    # @commands.command()
    # async def t(self, ctx, *, test=None):
    #     """TEST"""
    #     server = await ask_for_server(self.bot, ctx.message)
    #     if not server:
    #         return
    #     p = await Poll.load_from_db(self.bot, str(server.id), 'test', ctx=ctx)
    #     print(await Vote.load_number_of_voters_for_poll(self.bot, p.id))

    @app_commands.command(name="activate", description="Activate a prepared poll.")
    @app_commands.describe(
        short='Choose name of poll to activate',
    )
    async def activate(self, ctx, *, short: str=None):
        server = await ask_for_server(self.bot, ctx, short)
        if not server:
            return
        await ctx.response.defer(thinking=True)
            
        if not (isinstance(ctx.channel, discord.TextChannel) or isinstance(ctx.channel, discord.Thread)):
            await ctx.followup.send("`activate` can only be used in a server text channel.")
            return
        
        permissions = ctx.channel.permissions_for(server.me)
        if not permissions.embed_links or not permissions.manage_messages or not permissions.add_reactions or not permissions.read_message_history:
            await ctx.followup.send("Error: Missing permissions. Type \"/debug.\"")
            return
        
        guild = ctx.guild
        if not guild:
            await ctx.followup.send("Could not determine your server. Run the command in a server text channel.")
            return
        
        if short is None:
            pre = await get_server_pre(self.bot, ctx.guild)
            error = f'Please specify the label of a poll after the activate command. \n' \
                    f'~~`{pre}activate <poll_label>`~~ or `/activate <poll_label>`'
            await self.say_error(ctx, error)
        else:
            p = await Poll.load_from_db(self.bot, server.id, short)
            if p is not None:
                # check if already active, then just do nothing
                if await p.is_active():
                    return
                # Permission Check: Admin or Creator
                if not await self.is_admin_or_creator(
                        ctx, server,
                        p.author.id,
                        'You don\'t have sufficient rights to activate this poll. Please talk to the server admin.'
                ):
                    return

                # Activate Poll
                p.active = True
                await p.save_to_db()
                await self.show.callback(self, ctx, short=short)
            else:
                error = f'Poll with label "{short}" was not found. Listing prepared polls.'
                # pre = await get_server_pre(self.bot, ctx.message.server)
                # footer = f'Type {pre}show to display all polls'
                await self.say_error(ctx, error)
                #await ctx.invoke(self.show, 'prepared')
                await self.show.callback(self, ctx, short='prepared')

    @app_commands.command(name="delete", description="Delete a poll.")
    @app_commands.describe(
        short='Choose name of poll to delete',
    )
    async def delete(self, ctx, *, short: str=None):
        server = await ask_for_server(self.bot, ctx, short)
        if not server:
            return
        await ctx.response.defer(thinking=True)
            
        if not (isinstance(ctx.channel, discord.TextChannel) or isinstance(ctx.channel, discord.Thread)):
            await ctx.followup.send("`delete` can only be used in a server text channel.")
            return
            
        permissions = ctx.channel.permissions_for(server.me)
        if not permissions.embed_links or not permissions.manage_messages or not permissions.add_reactions or not permissions.read_message_history:
            await ctx.followup.send("Error: Missing permissions. Type \"/debug.\"")
            return
        
        guild = ctx.guild
        if not guild:
            await ctx.followup.send("Could not determine your server. Run the command in a server text channel.")
            return
        
        if short is None:
            pre = await get_server_pre(self.bot, ctx.guild)
            error = f'Please specify the label of a poll after the delete command. \n' \
                    f'~~`{pre}delete <poll_label>`~~ or `/delete <poll_label>`'
            await self.say_error(ctx, error)
        else:
            p = await Poll.load_from_db(self.bot, server.id, short)
            if p is not None:
                # Permission Check: Admin or Creator
                if not await self.is_admin_or_creator(
                        ctx, server,
                        p.author.id,
                        'You don\'t have sufficient rights to delete this poll. Please talk to the server admin.'
                ):
                    return False

                # Delete Poll and delete vote
                resultv2 = None
                resultv2 = await self.bot.db.polls.find_one({"server_id": str(server.id), 'short': short},{ "_id": 1, "server_id": 2, "short": 3 })
                result_vote = self.bot.db.votes.find({"poll_id": ObjectId(str(resultv2['_id']))},{ "poll_id": 1, "user_id": 2})
                if resultv2 is not None:
                    result_list_vote = [poll async for poll in result_vote.sort('poll_id', -1)]
                print('delete vote', result_list_vote, 'server_id:', server.id, 'short:', short)
                logger.info(f'deleted votes for poll ({short}). server_id: {server.id}, raw: {result_list_vote}')
                for i in range(len(result_list_vote)):
                    result_vote_delete = await self.bot.db.votes.delete_one({"poll_id": result_list_vote[i]['poll_id']})
                    if result_vote_delete.deleted_count == 1:
                        pass
                    else:
                        print('poll vote deleted failed!')
                        logger.error(f'poll vote deleted failed!: {resultv2}, server_id: {server.id}')
                
                result = await self.bot.db.polls.delete_one({'server_id': str(server.id), 'short': short})
                if result.deleted_count == 1:
                    say = f'Poll with label "{short}" was successfully deleted. This action can\'t be undone!'
                    title = 'Poll deleted'
                    await self.say_embed(ctx, say, title)
                else:
                    error = f'Action failed. Poll could not be deleted. ' \
                            f'You should probably report his error to the dev, thanks!'
                    await self.say_error(ctx, error)

            else:
                error = f'Poll with label "{short}" was not found.'
                pre = await get_server_pre(self.bot, ctx.guild)
                footer = f'Type ~~{pre}show~~ or /show to display all polls'
                await self.say_error(ctx, error, footer)

    @app_commands.command(name="close", description="Close a poll.")
    @app_commands.describe(
        short='Choose name of poll to close',
    )
    async def close(self, ctx, *, short: str=None):
        server = await ask_for_server(self.bot, ctx, short)
        if not server:
            return
        await ctx.response.defer(thinking=True)
            
        if not (isinstance(ctx.channel, discord.TextChannel) or isinstance(ctx.channel, discord.Thread)):
            await ctx.followup.send("`close` can only be used in a server text channel.")
            return
            
        permissions = ctx.channel.permissions_for(server.me)
        if not permissions.embed_links or not permissions.manage_messages or not permissions.add_reactions or not permissions.read_message_history:
            await ctx.followup.send("Error: Missing permissions. Type \"/debug.\"")
            return
        
        guild = ctx.guild
        if not guild:
            await ctx.followup.send("Could not determine your server. Run the command in a server text channel.")
            return
        
        if short is None:
            pre = await get_server_pre(self.bot, ctx.guild)
            error = f'Please specify the label of a poll after the close command. \n' \
                    f'~~`{pre}close <poll_label>`~~ or `/close <poll_label>`'
            await self.say_error(ctx, error)
        else:
            p = await Poll.load_from_db(self.bot, server.id, short)
            if p is not None:
                # Permission Check: Admin or Creator
                if not await self.is_admin_or_creator(
                        ctx, server,
                        p.author.id,
                        'You don\'t have sufficient rights to close this poll. Please talk to the server admin.'
                ):
                    return False

                # Close Poll
                p.open = False
                await p.save_to_db()
                await self.show.callback(self, ctx, short=short)
            else:
                error = f'Poll with label "{short}" was not found. Listing all open polls.'
                # pre = await get_server_pre(self.bot, ctx.message.server)
                # footer = f'Type {pre}show to display all polls'
                await self.say_error(ctx, error)
                await self.show.callback(self, ctx)

    @app_commands.command(name="copy", description="Copy a poll.")
    @app_commands.describe(
        short='Choose name of poll to copy',
    )
    async def copy(self, ctx, *, short: str=None):
        server = await ask_for_server(self.bot, ctx, short)
        if not server:
            return
        await ctx.response.defer(thinking=True)
            
        if not (isinstance(ctx.channel, discord.TextChannel) or isinstance(ctx.channel, discord.Thread)):
            await ctx.followup.send("`copy` can only be used in a server text channel.")
            return
            
        permissions = ctx.channel.permissions_for(server.me)
        if not permissions.embed_links or not permissions.manage_messages or not permissions.add_reactions or not permissions.read_message_history:
            await ctx.followup.send("Error: Missing permissions. Type \"/debug.\"")
            return
            
        guild = ctx.guild
        if not guild:
            await ctx.followup.send("Could not determine your server. Run the command in a server text channel.")
            return
        
        if short is None:
            pre = await get_server_pre(self.bot, ctx.guild)
            error = f'Please specify the label of a poll after the copy command. \n' \
                    f'~~`{pre}copy <poll_label>`~~ or `/copy <poll_label>`'
            await self.say_error(ctx, error)

        else:
            p = await Poll.load_from_db(self.bot, server.id, short)
            if p is not None:
                fix_cmd = p.to_command()
                replace_cmd = fix_cmd.replace('cmd', 'cmd:')
                text = await get_server_pre(self.bot, server) + p.to_command() + "\n\n /cmd " + replace_cmd
                await self.say_embed(ctx, text, title="Paste this to create a copy of the poll")
            else:
                error = f'Poll with label "{short}" was not found. Listing all open polls.'
                # pre = await get_server_pre(self.bot, ctx.message.server)
                # footer = f'Type {pre}show to display all polls'
                await self.say_error(ctx, error)
                await self.show.callback(self, ctx)

    @app_commands.command(name="export", description="Export a poll.")
    @app_commands.describe(
        short='Choose name of poll to export',
    )
    async def export(self, ctx, *, short: str=None):
        server = await ask_for_server(self.bot, ctx, short)
        if not server:
            return
        await ctx.response.defer(thinking=True)
            
        if not (isinstance(ctx.channel, discord.TextChannel) or isinstance(ctx.channel, discord.Thread)):
            await ctx.followup.send("`export` can only be used in a server text channel.")
            return
            
        permissions = ctx.channel.permissions_for(server.me)
        if not permissions.embed_links or not permissions.manage_messages or not permissions.add_reactions or not permissions.read_message_history:
            await ctx.followup.send("Error: Missing permissions. Type \"/debug.\"")
            return
            
        guild = ctx.guild
        if not guild:
            await ctx.followup.send("Could not determine your server. Run the command in a server text channel.")
            return
        
        if short is None:
            pre = await get_server_pre(self.bot, ctx.guild)
            error = f'Please specify the label of a poll after the export command. \n' \
                    f'~~`{pre}export <poll_label>`~~ or `/export <poll_label>`'
            await self.say_error(ctx, error)
        else:
            p = await Poll.load_from_db(self.bot, server.id, short)
            if p is not None:
                if p.open:
                    pre = await get_server_pre(self.bot, ctx.guild)
                    error_text = f'You can only export closed polls. \n' \
                                 f'Please ~~`{pre}close {short}`~~ or `/close {short}` the poll first or wait for the deadline.'
                    await self.say_error(ctx, error_text)
                else:
                    # sending file
                    await ctx.followup.send(f'Sending you the requested export of "{short}". check your DM')
                    file_name = await p.export()
                    if file_name is not None:
                        await ctx.user.send('Sending you the requested export of "{}".'.format(p.short),
                                                      file=discord.File(file_name)
                                                      )
                        # await self.bot.send_file(
                        #     ctx.message.author,
                        #     file_name,
                        #     content='Sending you the requested export of "{}".'.format(p.short)
                        # )
                    else:
                        error_text = 'Could not export the requested poll. \nPlease report this to the developer.'
                        await self.say_error(ctx, error_text)
            else:
                error = f'Poll with label "{short}" was not found.'
                # pre = await get_server_pre(self.bot, ctx.message.server)
                # footer = f'Type {pre}show to display all polls'
                await self.say_error(ctx, error)
                await self.show.callback(self, ctx)

    @app_commands.command(name="show", description="Show a list of open polls or show a specific poll.")
    @app_commands.describe(
        short='Parameters: "open" (default), "closed", "prepared" or <label>',
    )
    async def show(self, ctx, short: str='open', start: int=0):
        server = await ask_for_server(self.bot, ctx, short)
        if not server:
            return
        try:
            await ctx.response.defer(thinking=True)
        except discord.errors.InteractionResponded:
            print("show command skip thinking")
        if not (isinstance(ctx.channel, discord.TextChannel) or isinstance(ctx.channel, discord.Thread)):
            await ctx.followup.send("`show` can only be used in a server text channel.")
            return
        
        permissions = ctx.channel.permissions_for(server.me)
        if not permissions.embed_links or not permissions.manage_messages or not permissions.add_reactions or not permissions.read_message_history:
            await ctx.followup.send("Error: Missing permissions. Type \"/debug.\"")
            return
        
        guild = ctx.guild
        if not guild:
            await ctx.followup.send("Could not determine your server. Run the command in a server text channel.")
            return
        
        if short in ['open', 'closed', 'prepared']:
            query = None
            if short == 'open':
                query = self.bot.db.polls.find({'server_id': str(server.id), 'open': True, 'active': True})
            elif short == 'closed':
                query = self.bot.db.polls.find({'server_id': str(server.id), 'open': False, 'active': True})
            elif short == 'prepared':
                query = self.bot.db.polls.find({'server_id': str(server.id), 'active': False})

            if query is not None:
                # sort by newest first
                polls = [poll async for poll in query.sort('_id', -1)]
            else:
                return

            def item_fct(i, item):
                item["name"] = regex.sub("\n", " >> ", item["name"])
                return f':black_small_square: **{item["short"]}**: {item["name"]}'

            title = f' Listing {short} polls'
            embed = discord.Embed(title='', description='', colour=SETTINGS.color)
            embed.set_author(name=title, icon_url=SETTINGS.author_icon)
            # await self.bot.say(embed=await self.embed_list_paginated(polls, item_fct, embed))
            # msg = await self.embed_list_paginated(ctx, polls, item_fct, embed, per_page=8)
            pre = await get_server_pre(self.bot, server)
            footer_text = f'type {pre}show <label> or /show <label> to display a poll. '
            msg = await embed_list_paginated(ctx, self.bot, pre, polls, item_fct, embed, footer_prefix=footer_text,
                                             per_page=10)
        else:
            p = await Poll.load_from_db(self.bot, server.id, short)
            if p is not None:
                error_msg = 'This poll is inactive and you have no rights to display or view it.'
                if not await p.is_active() and not await self.is_admin_or_creator(ctx, server, p.author, error_msg):
                    return
                await p.post_embed(ctx)
            else:
                error = f'Poll with label {short} was not found.'
                pre = await get_server_pre(self.bot, server)
                footer = f'Type {pre}show or /show to display all polls'
                await self.say_error(ctx, error, footer)

    @app_commands.command(name="draw")
    async def draw(self, ctx, short: str=None, opt: str=None):
        server = await ask_for_server(self.bot, ctx, short)
        if not server:
            return
        await ctx.response.defer(thinking=True)
        if not (isinstance(ctx.channel, discord.TextChannel) or isinstance(ctx.channel, discord.Thread)):
            await ctx.followup.send("`draw` can only be used in a server text channel.")
            return
            
        permissions = ctx.channel.permissions_for(server.me)
        if not permissions.embed_links or not permissions.manage_messages or not permissions.add_reactions or not permissions.read_message_history:
            await ctx.followup.send("Error: Missing permissions. Type \"/debug.\"")
            return
        
        guild = ctx.guild
        if not guild:
            await ctx.followup.send("Could not determine your server. Run the command in a server text channel.")
            return
        
        pre = await get_server_pre(self.bot, ctx.guild)
        if opt is None:
            error = f'No answer specified please use the following syntax: \n' \
                    f'~~`{pre}draw <poll_label> <answer_letter>`~~ or `/draw <poll_label> <answer_letter>`'
            await self.say_error(ctx, error)
            return
        if short is None:
            error = f'Please specify the label of a poll after the export command. \n' \
                    f'~~`{pre}export <poll_label>`~~ or `/export <poll_label>`'
            await self.say_error(ctx, error)
            return

        p = await Poll.load_from_db(self.bot, server.id, short)
        if p is not None:
            if opt=='🎉' and p.options_reaction==['🎉']:
                error = f'Insufficient permissions for this command.'
                if not await self.is_admin_or_creator(ctx, server, p.author.id, error_msg=error):
                    return
                try:
                    choice = 0
                except ValueError:
                    choice = 99
                if len(p.options_reaction) <= choice:
                    error = f'Invalid answer "{opt}"...'
                    await self.say_error(ctx, error)
                    return
                if p.open:
                    error = f'Poll need to be closed!\nuse `/close` to close poll.'
                    await self.say_error(ctx, error)
                    return
                await p.load_full_votes()
                voter_list = []
                for vote in p.full_votes:
                    if vote.choice == choice:
                        voter_list.append(vote.user_id)
                if not voter_list:
                    error = f'No votes for option "{opt}".'
                    await self.say_error(ctx, error)
                    return
                print('voter_list', voter_list)
                winner_id = random.choice(voter_list)
                # winner = server.get_member(int(winner_id))
                # winner = await self.bot.fetch_user(int(winner_id))
                winner = await self.bot.member_cache.get(server, int(winner_id))
                if not winner:
                    error = f'Invalid winner drawn (id: {winner_id}).'
                    await self.say_error(ctx, error)
                    return
                text = f'The winner is: {winner.mention}'
                title = f'Drawing a random winner from "{opt.upper()}"...'
                return await self.say_embed(ctx, text, title=title)
            if p.options_reaction_default or p.options_reaction_emoji_only:
                error = f'Can\'t draw from emoji-only polls.'
                await self.say_error(ctx, error)
                return
            error = f'Insufficient permissions for this command.'
            if not await self.is_admin_or_creator(ctx, server, p.author.id, error_msg=error):
                return
            try:
                choice = ascii_lowercase.index(opt.lower())
            except ValueError:
                choice = 99
            if len(p.options_reaction) <= choice:
                error = f'Invalid answer "{opt}".'
                await self.say_error(ctx, error)
                return
            if p.open:
                error = f'Poll need to be closed!\nuse `/close` to close poll.'
                await self.say_error(ctx, error)
                return
            await p.load_full_votes()
            voter_list = []
            for vote in p.full_votes:
                if vote.choice == choice:
                    voter_list.append(vote.user_id)
            if not voter_list:
                error = f'No votes for option "{opt}".'
                await self.say_error(ctx, error)
                return
            # print(voter_list)
            winner_id = random.choice(voter_list)
            # winner = server.get_member(int(winner_id))
            # winner = await self.bot.fetch_user(int(winner_id))
            winner = await self.bot.member_cache.get(server, int(winner_id))
            if not winner:
                error = f'Invalid winner drawn (id: {winner_id}).'
                await self.say_error(ctx, error)
                return
            text = f'The winner is: {winner.mention}'
            title = f'Drawing a random winner from "{opt.upper()}"...'
            await self.say_embed(ctx, text, title=title)
        else:
            error = f'Poll with label "{short}" was not found.'
            await self.say_error(ctx, error)
            await self.show.callback(self, ctx)

    @app_commands.command(name="cmd", description="The old, command style way paired with the wizard.")
    async def cmd(self, ctx, *, cmd: str=None):
        # await self.say_embed(ctx, say_text='This command is temporarily disabled.')

        server = await ask_for_server(self.bot, ctx)
        if not server:
            return
        await ctx.response.defer(thinking=True)
        if not (isinstance(ctx.channel, discord.TextChannel) or isinstance(ctx.channel, discord.Thread)):
            await ctx.followup.send("`cmd` can only be used in a server text channel.")
            return
            
        permissions = ctx.channel.permissions_for(server.me)
        if not permissions.embed_links or not permissions.manage_messages or not permissions.add_reactions or not permissions.read_message_history:
            await ctx.followup.send("Error: Missing permissions. Type \"/debug.\"")
            return
        
        guild = ctx.guild
        if not guild:
            await ctx.followup.send("Could not determine your server. Run the command in a server text channel.")
            return
        
        pre = await get_server_pre(self.bot, server)
        try:
            # generate the argparser and handle invalid stuff
            descr = 'Accept poll settings via commandstring. \n\n' \
                    '**Wrap all arguments in quotes like this:** \n' \
                    f'{pre}cmd -question \"What tea do you like?\" -o \"green, black, chai\"\n\n' \
                    'The Order of arguments doesn\'t matter. If an argument is missing, it will use the default value. ' \
                    'If an argument is invalid, the wizard will step in. ' \
                    'If the command string is invalid, you will get this error :)'
            parser = argparse.ArgumentParser(description=descr, formatter_class=CustomFormatter, add_help=False)
            parser.add_argument('-question', '-q')
            parser.add_argument('-label', '-l', default=str(await generate_word(self.bot, server.id)))
            parser.add_argument('-anonymous', '-a', action="store_true")
            parser.add_argument('-options', '-o')
            parser.add_argument('-survey_flags', '-sf', default='0')
            parser.add_argument('-multiple_choice', '-mc', default='1')
            parser.add_argument('-hide_votes', '-h', action="store_true")
            parser.add_argument('-roles', '-r', default='all')
            parser.add_argument('-weights', '-w', default='none')
            parser.add_argument('-prepare', '-p', default='-1')
            parser.add_argument('-deadline', '-d', default='0')

            helpstring = parser.format_help()
            helpstring = helpstring.replace("pollmaster.py", f"{pre}cmd ")

            if not cmd or len(cmd) < 2 or cmd == 'help':
                # Shlex will block if the string is empty
                await self.say_embed(ctx, say_text=helpstring)
                return

            try:
                # print(cmd)
                cmd = cmd.replace('“', '"')  # fix for iphone keyboard
                cmd = cmd.replace('”', '"')  # fix for iphone keyboard
                # print(cmd)
                cmds = shlex.split(cmd)
            except ValueError:
                await self.say_error(ctx, error_text=helpstring)
                return
            except:
                return

            try:
                args, unknown_args = parser.parse_known_args(cmds)
            except SystemExit:
                await self.say_error(ctx, error_text=helpstring)
                return
            except:
                return

            if unknown_args:
                error_text = f'**There was an error reading the command line options!**.\n' \
                             f'Most likely this is because you didn\'t surround the arguments with double quotes like this: ' \
                             f'`{pre}cmd -q "question of the poll" -o "yes, no, maybe"`' \
                             f'\n\nHere are the arguments I could not understand:\n'
                error_text += '`' + '\n'.join(unknown_args) + '`'
                error_text += f'\n\nHere are the arguments which are ok:\n'
                error_text += '`' + '\n'.join([f'{k}: {v}' for k, v in vars(args).items()]) + '`'

                await self.say_error(ctx, error_text=error_text, footer_text=f'type `{pre}cmd help` for details.')
                return

            # pass arguments to the wizard
            async def route(poll):
                await poll.set_name(ctx, force=args.question)
                await poll.set_short(ctx, force=args.label)
                await poll.set_anonymous(ctx, force=f'{"yes" if args.anonymous else "no"}')
                await poll.set_options_reaction(ctx, force=args.options)
                await poll.set_survey_flags(ctx, force=args.survey_flags)
                await poll.set_multiple_choice(ctx, force=args.multiple_choice)
                await poll.set_hide_vote_count(ctx, force=f'{"yes" if args.hide_votes else "no"}')
                await poll.set_roles(ctx, force=args.roles)
                await poll.set_weights(ctx, force=args.weights)
                await poll.set_preparation(ctx, force=args.prepare)
                await poll.set_thumbnail(ctx, force='0')
                await poll.set_duration(ctx, force=args.deadline)

            poll = await self.wizard(ctx, route, server)
            if poll:
                await poll.post_embed(poll.channel)

        except Exception as error:
            logger.error("ERROR IN pm!cmd")
            logger.exception(error)

    @app_commands.command(name="quick", description="Create a quick poll with just a question and some options. (Wizard)")
    @app_commands.describe(
        name='(optional) **What is the question of your poll?** Try to be descriptive without writing more than one sentence.',
        channel_id='(optional) choose a channel that you want the poll to be send to.',
        
    )
    async def quick(self, ctx, *, name: str=None, channel_id: discord.TextChannel = None):
        server = await ask_for_server(self.bot, ctx)
        if not server:
            return
        await ctx.response.defer(thinking=True)
        if not (isinstance(ctx.channel, discord.TextChannel) or isinstance(ctx.channel, discord.Thread)):
            await ctx.followup.send("`quick` can only be used in a server text channel.")
            return
        permissions = ctx.channel.permissions_for(server.me)
        if not permissions.embed_links or not permissions.manage_messages or not permissions.add_reactions or not permissions.read_message_history:
            await ctx.followup.send("Error: Missing permissions. Type \"/debug.\"")
            return
            
        if channel_id != None:
            #getchannel = self.bot.get_channel(channel_id)
            #print("getchannel", channel_id, ctx.user)
            userpermissions = channel_id.permissions_for(ctx.user)
            if not userpermissions.send_messages:
                await ctx.followup.send(f"Error: you don't have permissions to send messages in channel <#{channel_id.id}>.")
                return
            permissionsv2 = channel_id.permissions_for(server.me)
            if not permissionsv2.embed_links or not permissionsv2.manage_messages or not permissionsv2.add_reactions or not permissionsv2.read_message_history:
                await ctx.followup.send(f"Error: Missing permissions in channel <#{channel_id.id}>. Type \"/debug.\" in that channel")
                return
        
        guild = ctx.guild
        if not guild:
            await ctx.followup.send("Could not determine your server. Run the command in a server text channel.")
            return
        async def route(poll):
            await poll.set_name(ctx, force=name)
            await poll.set_short(ctx, force=str(await generate_word(self.bot, server.id)))
            await poll.set_anonymous(ctx, force='no')
            await poll.set_options_reaction(ctx)
            await poll.set_multiple_choice(ctx, force='1')
            await poll.set_hide_vote_count(ctx, force='no')
            await poll.set_roles(ctx, force='all')
            await poll.set_weights(ctx, force='none')
            await poll.set_thumbnail(ctx, force='0')
            await poll.set_duration(ctx, force='0')

        poll = await self.wizard(ctx, route, server, channel_id=channel_id)
        if poll:
            await poll.post_embed(poll.channel)
            
    @app_commands.command(name="quickslash", description="quick poll with just a question and some options. (slash only no Wizard)")
    @app_commands.describe(
        name='**What is the question of your poll?** Try to be descriptive without writing more than one sentence.',
        options_reaction=f'**Choose the options/answers for your poll.** Either chose a preset of options or type your own options, separated by commas. **1** - :white_check_mark: :negative_squared_cross_mark: **2** - :thumbsup: :zipper_mouth: :thumbsdown: **3** - :heart_eyes: :thumbsup: :zipper_mouth:  :thumbsdown: :nauseated_face: **4** - in favour, against, abstaining. Example for custom options: **apple juice, banana ice cream, kiwi slices**',
    )
    async def quickslash(self, ctx, *, name: str, options_reaction: str):
        server = await ask_for_server(self.bot, ctx)
        if not server:
            return
        await ctx.response.defer(thinking=True)
        if not (isinstance(ctx.channel, discord.TextChannel) or isinstance(ctx.channel, discord.Thread)):
            await ctx.followup.send("`quickslash` can only be used in a server text channel.")
            return
        permissions = ctx.channel.permissions_for(server.me)
        if not permissions.embed_links or not permissions.manage_messages or not permissions.add_reactions or not permissions.read_message_history:
            await ctx.followup.send("Error: Missing permissions. Type \"/debug.\"")
            return
        
        guild = ctx.guild
        if not guild:
            await ctx.followup.send("Could not determine your server. Run the command in a server text channel.")
            return
        
        async def route(poll):
            await poll.set_name(ctx, force=name)
            await poll.set_short(ctx, force=str(await generate_word(self.bot, server.id)))
            await poll.set_anonymous(ctx, force='no')
            await poll.set_options_reaction(ctx, force=options_reaction)
            await poll.set_multiple_choice(ctx, force='1')
            await poll.set_hide_vote_count(ctx, force='no')
            await poll.set_roles(ctx, force='all')
            await poll.set_weights(ctx, force='none')
            await poll.set_thumbnail(ctx, force='0')
            await poll.set_duration(ctx, force='0')

        poll = await self.wizard(ctx, route, server)
        if poll:
            await poll.post_embed(poll.channel)

    @app_commands.command(name="prepare", description="Prepare a poll to use later. (Wizard)")
    @app_commands.describe(
        name='(optional) **What is the question of your poll?** Try to be descriptive without writing more than one sentence.',
        channel_id='(optional) choose a channel that you want the poll to be send to.',
    )
    async def prepare(self, ctx, *, name: str=None, channel_id: discord.TextChannel = None):
        server = await ask_for_server(self.bot, ctx)
        if not server:
            return
        await ctx.response.defer(thinking=True)
        if not (isinstance(ctx.channel, discord.TextChannel) or isinstance(ctx.channel, discord.Thread)):
            await ctx.followup.send("`prepare` can only be used in a server text channel.")
            return
        permissions = ctx.channel.permissions_for(server.me)
        if not permissions.embed_links or not permissions.manage_messages or not permissions.add_reactions or not permissions.read_message_history:
            await ctx.followup.send("Error: Missing permissions. Type \"/debug.\"")
            return
            
        if channel_id != None:
            #getchannel = self.bot.get_channel(channel_id)
            #print("getchannel", channel_id, ctx.user)
            userpermissions = channel_id.permissions_for(ctx.user)
            if not userpermissions.send_messages:
                await ctx.followup.send(f"Error: you don't have permissions to send messages in channel <#{channel_id.id}>.")
                return
            permissionsv2 = channel_id.permissions_for(server.me)
            if not permissionsv2.embed_links or not permissionsv2.manage_messages or not permissionsv2.add_reactions or not permissionsv2.read_message_history:
                await ctx.followup.send(f"Error: Missing permissions in channel <#{channel_id.id}>. Type \"/debug.\" in that channel")
                return
        
        guild = ctx.guild
        if not guild:
            await ctx.followup.send("Could not determine your server. Run the command in a server text channel.")
            return
        async def route(poll):
            await poll.set_name(ctx, force=name)
            await poll.set_short(ctx)
            await poll.set_preparation(ctx)
            await poll.set_anonymous(ctx)
            await poll.set_options_reaction(ctx)
            await poll.set_survey_flags(ctx)
            await poll.set_multiple_choice(ctx)
            await poll.set_hide_vote_count(ctx)
            await poll.set_roles(ctx)
            await poll.set_weights(ctx)
            await poll.set_thumbnail(ctx)
            await poll.set_duration(ctx)

        poll = await self.wizard(ctx, route, server, channel_id=channel_id)
        if poll:
            await poll.post_embed(ctx.user)
            
    @app_commands.command(name="prepareslash", description="Prepare a poll to use later. (slash only no Wizard)")
    @app_commands.describe(
        name='**What is the question of your poll?** Try to be descriptive without writing more than one sentence.',
        short='**Now type a unique one word identifier, a label, for your poll.** This label will be used to refer to the poll. Keep it short and significant.',
        preparation='This poll will be created inactive. You can either schedule activation at a certain date or activate it manually. **Type `0` to activate it manually or tell me when you want to activate it** by typing an absolute or relative date. You can specify a timezone if you want. Examples: `in 2 days`, `next week CET`, `may 3rd 2019`, `9.11.2019 9pm EST` ',
        anonymous='**Do you want your poll to be anonymous?** (0 - No, 1 - Yes) An anonymous poll has the following effects: 🔹 You will never see who voted for which option 🔹 Once the poll is closed, you will see who participated (but not their choice)',
        options_reaction=f'**Choose the options/answers for your poll.** Either chose a preset of options or type your own options, separated by commas. **1** - :white_check_mark: :negative_squared_cross_mark: **2** - :thumbsup: :zipper_mouth: :thumbsdown: **3** - :heart_eyes: :thumbsup: :zipper_mouth:  :thumbsdown: :nauseated_face: **4** - in favour, against, abstaining. Example for custom options: **apple juice, banana ice cream, kiwi slices**',
        survey_flags='**Which options should ask the user for a custom answer?** Type `0` to skip survey options. If you want multiple survey options, separate the numbers with a comma. `0 - None (classic poll)`',
        multiple_choice='**How many options should the voters be able choose?** `0 - No Limit: Multiple Choice` `1  - Single Choice` `2+  - Specify exactly how many Choices` If the maximum choices are reached for a voter, they have to unvote an option before being able to vote for a different one.',
        hide_vote_count='**Do you want to hide the live vote count?** `0 - No, show it (Default)` `1  - Yes, hide it` You will still be able to see the vote count once the poll is closed. This settings will just hide the vote count while the poll is active.',
        roles='**Choose which roles are allowed to vote.** Type `0`, `all` or `everyone` to have no restrictions. If you want multiple roles to be able to vote, separate the numbers with a comma.',
        weights='**Weights allow you to give certain roles more or less effective votes. Type `0` or `none` if you don\'t need any weights.** A weight for the role `moderator` of `2` for example will automatically count the votes of all the moderators twice. To assign weights type the role, followed by a colon, followed by the weight like this: `moderator: 2, newbie: 0.5`',
        duration='**When should the poll be closed?** If you want the poll to last indefinitely (until you close it), type `0`. Otherwise tell me when the poll should close in relative or absolute terms. You can specify a timezone if you want. Examples: `in 6 hours` or `next week CET` or `aug 15th 5:10` or `15.8.2019 11pm EST`',
    )
    @app_commands.choices(
        anonymous=[discord.app_commands.Choice(name='0', value=1), discord.app_commands.Choice(name='1', value=2), discord.app_commands.Choice(name='yes', value=3), discord.app_commands.Choice(name='no', value=4)],
        hide_vote_count=[discord.app_commands.Choice(name='0', value=1), discord.app_commands.Choice(name='1', value=2), discord.app_commands.Choice(name='yes', value=3), discord.app_commands.Choice(name='no', value=4)],
    )
    async def prepareslash(self, ctx, *, name: str, short: str, preparation: str, anonymous: discord.app_commands.Choice[int], options_reaction: str, survey_flags: str, multiple_choice: str, hide_vote_count: discord.app_commands.Choice[int], roles: str, weights: str, duration: str):
        server = await ask_for_server(self.bot, ctx)
        if not server:
            return
        await ctx.response.defer(thinking=True)
        if not (isinstance(ctx.channel, discord.TextChannel) or isinstance(ctx.channel, discord.Thread)):
            await ctx.followup.send("`prepareslash` can only be used in a server text channel.")
            return
        
        permissions = ctx.channel.permissions_for(server.me)
        if not permissions.embed_links or not permissions.manage_messages or not permissions.add_reactions or not permissions.read_message_history:
            await ctx.followup.send("Error: Missing permissions. Type \"/debug.\"")
            return
        
        guild = ctx.guild
        if not guild:
            await ctx.followup.send("Could not determine your server. Run the command in a server text channel.")
            return
        
        async def route(poll):
            await poll.set_name(ctx, force=name)
            await poll.set_short(ctx, force=short)
            await poll.set_preparation(ctx, force=preparation)
            await poll.set_anonymous(ctx, force=anonymous.name)
            await poll.set_options_reaction(ctx, force=options_reaction)
            await poll.set_survey_flags(ctx, force=survey_flags)
            await poll.set_multiple_choice(ctx, force=multiple_choice)
            await poll.set_hide_vote_count(ctx, force=hide_vote_count.name)
            await poll.set_roles(ctx, force=roles)
            await poll.set_weights(ctx, force=weights)
            await poll.set_thumbnail(ctx, force='0')
            await poll.set_duration(ctx, force=duration)

        poll = await self.wizard(ctx, route, server)
        if poll:
            await poll.post_embed(ctx.user)

    @app_commands.command(name="advanced", description="Poll with more options. (Wizard)")
    @app_commands.describe(
        name='(optional) **What is the question of your poll?** Try to be descriptive without writing more than one sentence.',
        channel_id='(optional) choose a channel that you want the poll to be send to.',
    )
    async def advanced(self, ctx, *, name: str=None, channel_id: discord.TextChannel = None):
        server = await ask_for_server(self.bot, ctx)
        if not server:
            return
        await ctx.response.defer(thinking=True)
        if not (isinstance(ctx.channel, discord.TextChannel) or isinstance(ctx.channel, discord.Thread)):
            await ctx.followup.send("`advanced` can only be used in a server text channel.")
            return
        permissions = ctx.channel.permissions_for(server.me)
        if not permissions.embed_links or not permissions.manage_messages or not permissions.add_reactions or not permissions.read_message_history:
            await ctx.followup.send("Error: Missing permissions. Type \"/debug.\"")
            return
            
        if channel_id != None:
            #getchannel = self.bot.get_channel(channel_id)
            #print("getchannel", channel_id, ctx.user)
            userpermissions = channel_id.permissions_for(ctx.user)
            if not userpermissions.send_messages:
                await ctx.followup.send(f"Error: you don't have permissions to send messages in channel <#{channel_id.id}>.")
                return
            permissionsv2 = channel_id.permissions_for(server.me)
            if not permissionsv2.embed_links or not permissionsv2.manage_messages or not permissionsv2.add_reactions or not permissionsv2.read_message_history:
                await ctx.followup.send(f"Error: Missing permissions in channel <#{channel_id.id}>. Type \"/debug.\" in that channel")
                return
        
        guild = ctx.guild
        if not guild:
            await ctx.followup.send("Could not determine your server. Run the command in a server text channel.")
            return
        async def route(poll):
            await poll.set_name(ctx, force=name)
            await poll.set_short(ctx)
            await poll.set_anonymous(ctx)
            await poll.set_options_reaction(ctx)
            await poll.set_survey_flags(ctx)
            await poll.set_multiple_choice(ctx)
            await poll.set_hide_vote_count(ctx)
            await poll.set_roles(ctx)
            await poll.set_weights(ctx)
            await poll.set_thumbnail(ctx)
            await poll.set_duration(ctx)
        poll = await self.wizard(ctx, route, server, channel_id=channel_id)
        if poll:
            await poll.post_embed(poll.channel)
            
    @app_commands.command(name="advancedslash", description="Poll with more options. (slash only no Wizard)")
    @app_commands.describe(
        name='**What is the question of your poll?** Try to be descriptive without writing more than one sentence.',
        short='**Now type a unique one word identifier, a label, for your poll.** This label will be used to refer to the poll. Keep it short and significant.',
        anonymous='**Do you want your poll to be anonymous?** (0 - No, 1 - Yes) An anonymous poll has the following effects: 🔹 You will never see who voted for which option 🔹 Once the poll is closed, you will see who participated (but not their choice)',
        options_reaction=f'**Choose the options/answers for your poll.** Either chose a preset of options or type your own options, separated by commas. **1** - :white_check_mark: :negative_squared_cross_mark: **2** - :thumbsup: :zipper_mouth: :thumbsdown: **3** - :heart_eyes: :thumbsup: :zipper_mouth:  :thumbsdown: :nauseated_face: **4** - in favour, against, abstaining. Example for custom options: **apple juice, banana ice cream, kiwi slices**',
        survey_flags='**Which options should ask the user for a custom answer?** Type `0` to skip survey options. If you want multiple survey options, separate the numbers with a comma. `0 - None (classic poll)`',
        multiple_choice='**How many options should the voters be able choose?** `0 - No Limit: Multiple Choice` `1  - Single Choice` `2+  - Specify exactly how many Choices` If the maximum choices are reached for a voter, they have to unvote an option before being able to vote for a different one.',
        hide_vote_count='**Do you want to hide the live vote count?** `0 - No, show it (Default)` `1  - Yes, hide it` You will still be able to see the vote count once the poll is closed. This settings will just hide the vote count while the poll is active.',
        roles='**Choose which roles are allowed to vote.** Type `0`, `all` or `everyone` to have no restrictions. If you want multiple roles to be able to vote, separate the numbers with a comma.',
        weights='**Weights allow you to give certain roles more or less effective votes. Type `0` or `none` if you don\'t need any weights.** A weight for the role `moderator` of `2` for example will automatically count the votes of all the moderators twice. To assign weights type the role, followed by a colon, followed by the weight like this: `moderator: 2, newbie: 0.5`',
        duration='**When should the poll be closed?** If you want the poll to last indefinitely (until you close it), type `0`. Otherwise tell me when the poll should close in relative or absolute terms. You can specify a timezone if you want. Examples: `in 6 hours` or `next week CET` or `aug 15th 5:10` or `15.8.2019 11pm EST`',
    )
    @app_commands.choices(
        anonymous=[discord.app_commands.Choice(name='0', value=1), discord.app_commands.Choice(name='1', value=2), discord.app_commands.Choice(name='yes', value=3), discord.app_commands.Choice(name='no', value=4)],
        hide_vote_count=[discord.app_commands.Choice(name='0', value=1), discord.app_commands.Choice(name='1', value=2), discord.app_commands.Choice(name='yes', value=3), discord.app_commands.Choice(name='no', value=4)],
    )
    async def advancedslash(self, ctx, *, name: str, short: str, anonymous: discord.app_commands.Choice[int], options_reaction: str, survey_flags: str, multiple_choice: str, hide_vote_count: discord.app_commands.Choice[int], roles: str, weights: str, duration: str):
        server = await ask_for_server(self.bot, ctx)
        if not server:
            return
        await ctx.response.defer(thinking=True)
        if not (isinstance(ctx.channel, discord.TextChannel) or isinstance(ctx.channel, discord.Thread)):
            await ctx.followup.send("`advancedslash` can only be used in a server text channel.")
            return
        permissions = ctx.channel.permissions_for(server.me)
        if not permissions.embed_links or not permissions.manage_messages or not permissions.add_reactions or not permissions.read_message_history:
            await ctx.followup.send("Error: Missing permissions. Type \"/debug.\"")
            return
        
        guild = ctx.guild
        if not guild:
            await ctx.followup.send("Could not determine your server. Run the command in a server text channel.")
            return
        
        async def route(poll):
            await poll.set_name(ctx, force=name)
            await poll.set_short(ctx, force=short)
            await poll.set_anonymous(ctx, force=anonymous.name)
            await poll.set_options_reaction(ctx, force=options_reaction)
            await poll.set_survey_flags(ctx, force=survey_flags)
            await poll.set_multiple_choice(ctx, force=multiple_choice)
            await poll.set_hide_vote_count(ctx, force=hide_vote_count.name)
            await poll.set_roles(ctx, force=roles)
            await poll.set_weights(ctx, force=weights)
            await poll.set_thumbnail(ctx, force='0')
            await poll.set_duration(ctx, force=duration)

        poll = await self.wizard(ctx, route, server)
        if poll:
            await poll.post_embed(poll.channel)

    @app_commands.command(name="new", description="Start the poll wizard to create a new poll step by step. (Wizard)" )
    @app_commands.describe(
        name='(optional) **What is the question of your poll?** Try to be descriptive without writing more than one sentence.',
        channel_id='(optional) choose a channel that you want the poll to be send to.',
    )
    # @app_commands.choices(
    #     anonymous=[discord.app_commands.Choice(name='0', value=1), discord.app_commands.Choice(name='1', value=2), discord.app_commands.Choice(name='yes', value=3), discord.app_commands.Choice(name='no', value=4)]
    # )
    async def new(self, ctx, *, name: str=None, channel_id: discord.TextChannel = None):
        server = await ask_for_server(self.bot, ctx)
        if not server:
            return
        await ctx.response.defer(thinking=True)
        #channel_id=None #temp
        mention=None
        if not (isinstance(ctx.channel, discord.TextChannel) or isinstance(ctx.channel, discord.Thread)):
            await ctx.followup.send("`new` can only be used in a server text channel.")
            return
        permissions = ctx.channel.permissions_for(server.me)
        if not permissions.embed_links or not permissions.manage_messages or not permissions.add_reactions or not permissions.read_message_history:
            await ctx.followup.send("Error: Missing permissions. Type \"/debug.\"")
            return
        if channel_id != None:
            #getchannel = self.bot.get_channel(channel_id)
            #print("getchannel", channel_id, ctx.user)
            userpermissions = channel_id.permissions_for(ctx.user)
            if not userpermissions.send_messages:
                await ctx.followup.send(f"Error: you don't have permissions to send messages in channel <#{channel_id.id}>.")
                return
            permissionsv2 = channel_id.permissions_for(server.me)
            if not permissionsv2.embed_links or not permissionsv2.manage_messages or not permissionsv2.add_reactions or not permissionsv2.read_message_history:
                await ctx.followup.send(f"Error: Missing permissions in channel <#{channel_id.id}>. Type \"/debug.\" in that channel")
                return
        
        guild = ctx.guild #= server #maybe?
        if not guild:
            await ctx.followup.send("Could not determine your server. Run the command in a server text channel.")
            return
        async def route(poll):
            await poll.set_name(ctx, force=name)
            await poll.set_short(ctx)
            await poll.set_anonymous(ctx)
            await poll.set_options_reaction(ctx)
            await poll.set_survey_flags(ctx, force='0')
            await poll.set_multiple_choice(ctx)
            await poll.set_hide_vote_count(ctx, force='no')
            await poll.set_roles(ctx, force='all')
            await poll.set_weights(ctx, force='none')
            await poll.set_thumbnail(ctx, force='0')
            await poll.set_duration(ctx)

        poll = await self.wizard(ctx, route, server, channel_id=channel_id, mention_role=mention)
        if poll:
            await poll.post_embed(poll.channel)
            
    @app_commands.command(name="newslash", description="to create a new poll. (slash only no wizard) ")
    @app_commands.describe(
        name='**What is the question of your poll?** Try to be descriptive without writing more than one sentence.',
        short='**Now type a unique one word identifier, a label, for your poll.** This label will be used to refer to the poll. Keep it short and significant.',
        anonymous='**Do you want your poll to be anonymous?** (0 - No, 1 - Yes) An anonymous poll has the following effects: 🔹 You will never see who voted for which option 🔹 Once the poll is closed, you will see who participated (but not their choice)',
        options_reaction=f'**Choose the options/answers for your poll.** Either chose a preset of options or type your own options, separated by commas. **1** - :white_check_mark: :negative_squared_cross_mark: **2** - :thumbsup: :zipper_mouth: :thumbsdown: **3** - :heart_eyes: :thumbsup: :zipper_mouth:  :thumbsdown: :nauseated_face: **4** - in favour, against, abstaining. Example for custom options: **apple juice, banana ice cream, kiwi slices**',
        multiple_choice='**How many options should the voters be able choose?** `0 - No Limit: Multiple Choice` `1  - Single Choice` `2+  - Specify exactly how many Choices` If the maximum choices are reached for a voter, they have to unvote an option before being able to vote for a different one.',
        duration='**When should the poll be closed?** If you want the poll to last indefinitely (until you close it), type `0`. Otherwise tell me when the poll should close in relative or absolute terms. You can specify a timezone if you want. Examples: `in 6 hours` or `next week CET` or `aug 15th 5:10` or `15.8.2019 11pm EST`',
    )
    @app_commands.choices(
        anonymous=[discord.app_commands.Choice(name='0', value=1), discord.app_commands.Choice(name='1', value=2), discord.app_commands.Choice(name='yes', value=3), discord.app_commands.Choice(name='no', value=4)],
    )
    async def newslash(self, ctx, *, name: str, short: str, anonymous: discord.app_commands.Choice[int], options_reaction: str, multiple_choice: str, duration: str):
        server = await ask_for_server(self.bot, ctx)
        if not server:
            return
        await ctx.response.defer(thinking=True)
        if not (isinstance(ctx.channel, discord.TextChannel) or isinstance(ctx.channel, discord.Thread)):
            await ctx.followup.send("`newslash` can only be used in a server text channel.")
            return
        permissions = ctx.channel.permissions_for(server.me)
        if not permissions.embed_links or not permissions.manage_messages or not permissions.add_reactions or not permissions.read_message_history:
            await ctx.followup.send("Error: Missing permissions. Type \"/debug.\"")
            return
        
        guild = ctx.guild
        if not guild:
            await ctx.followup.send("Could not determine your server. Run the command in a server text channel.")
            return
        
        async def route(poll):
            await poll.set_name(ctx, force=name)
            await poll.set_short(ctx, force=short)
            await poll.set_anonymous(ctx, force=anonymous.name)
            await poll.set_options_reaction(ctx, force=options_reaction)
            await poll.set_survey_flags(ctx, force='0')
            await poll.set_multiple_choice(ctx, force=multiple_choice)
            await poll.set_hide_vote_count(ctx, force='no')
            await poll.set_roles(ctx, force='all')
            await poll.set_weights(ctx, force='none')
            await poll.set_thumbnail(ctx, force='0')
            await poll.set_duration(ctx, force=duration)

        poll = await self.wizard(ctx, route, server)
        if poll:
            await poll.post_embed(poll.channel)

    # The Wizard!
    async def wizard(self, ctx, route, server, channel_id=None, mention_role=None):
        print('a wizard has started!')
        channel = await ask_for_channel(ctx, self.bot, server, ctx)
        if not channel:
            return

        pre = await get_server_pre(self.bot, server)
        #print('wiz get channel', channel_id)
        if channel_id == None:
            print('wiz get channel = ', channel_id)
            channel_id = channel
        #print('wiz get channelv2', channel_id) 
        if mention_role != None:
            print("wiz mention role", mention_role)
            mention_role = mention_role.id
        # Permission Check
        # member = server.get_member(ctx.message.author.id)
        member = ctx.user
        if not member.guild_permissions.manage_guild:
            result = await self.bot.db.config.find_one({'_id': str(server.id)})
            if result and result.get('admin_role') not in [r.name for r in member.roles] and result.get(
                    'user_role') not in [r.name for r in member.roles]:
                print("a wizard was canceled. user had no permission!")
                try:
                    await ctx.user.send('You don\'t have sufficient rights to start new polls on this server. '
                                                'A server administrator has to assign the user or admin role to you. '
                                                f'To view and set the permissions, an admin can use ~~`{pre}userrole` and '
                                                f'`{pre}adminrole`~~ or `/userrole` and `/adminrole`')
                    return
                except discord.Forbidden:
                    if result and not result.get('error_mess') or result and result.get('error_mess') == 'True':
                        errormessage = traceback.format_exc(limit=0)
                        embederror = discord.Embed(title='Poll Command Error', color=discord.Color.red())
                        if errormessage.find("Cannot send messages to this user") >= 0:
                            embederror.add_field(name=f'Error type:', value='Error: can\'t send you a DM. please allow DM for this bot!', inline=False )
                            embederror.set_footer(text=f'From poll: None \nThis message will self-destruct in 1 min.')
                            await channel.send(f"<@{ctx.user.id}> Error!", embed=embederror, delete_after=60)
                            return
                        else:
                            print('error = unknown', traceback.format_exc())
                            return
                    else:
                        return
                        

        # Create object
        poll = Poll(self.bot, ctx, server, channel=channel_id, ping_role=mention_role) #it worked!! channel= will need to be override

        # Route to define object, passed as argument for different constructors
        if ctx.message and ctx.message.content and not ctx.message.content.startswith(f'{pre}cmd '):
            poll.wizard_messages.append(ctx)
        try:
            await route(poll)
            poll.finalize()
            await poll.clean_up(ctx.channel)
        except StopWizard:
            print("a wizard was canceled!")
            await poll.clean_up(ctx.channel)
            return

        # Finalize
        await poll.save_to_db()
        print('a wizard has finished!', server.id)
        return poll

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, data):
        # get emoji symbol
        #print('reaction_remove ran!!', data)
        emoji = data.emoji
        if not emoji:
            return

        # check if removed by the bot.. this is a bit hacky but discord doesn't provide the correct info...
        message_id = data.message_id
        user_id = data.user_id
        if self.ignore_next_removed_reaction.get(str(message_id) + str(emoji)) == user_id:
            del self.ignore_next_removed_reaction[str(message_id) + str(emoji)]
            return

        # check if we can find a poll label
        message_id = data.message_id
        channel_id = data.channel_id
        channel = self.bot.get_channel(channel_id)
        #print('channel type remove', type(channel))
        if isinstance(channel, discord.TextChannel):
            server = channel.guild
            # user = server.get_member(user_id)
            # user = await self.bot.fetch_user(user_id)
            user = await self.bot.member_cache.get(server, user_id)
            message = self.bot.message_cache.get(message_id)
            #print('reactionremove textchannel ran!message', message, 'm_id', message_id)
            if message is None:
                try:
                    message = await channel.fetch_message(message_id)
                except discord.errors.Forbidden:
                    # Ignore Missing Access error
                    return
                self.bot.message_cache.put(message_id, message)
            if message.author.id != self.bot.user.id:
                #print("ignore message remove", message_id)
                return
            label = self.get_label(message)
            if not label:
                return
        elif isinstance(channel, discord.Thread):
            server = channel.guild
            # user = server.get_member(user_id)
            # user = await self.bot.fetch_user(user_id)
            user = await self.bot.member_cache.get(server, user_id)
            message = self.bot.message_cache.get(message_id)
            #print('reactionremove Thread ran!message', message, 'm_id', message_id)
            if message is None:
                try:
                    message = await channel.fetch_message(message_id)
                except discord.errors.Forbidden:
                    # Ignore Missing Access error
                    return
                self.bot.message_cache.put(message_id, message)
            if message.author.id != self.bot.user.id:
                #print("ignore message remove", message_id)
                return
            label = self.get_label(message)
            if not label:
                return
        elif isinstance(channel, discord.DMChannel):
            user = await self.bot.fetch_user(user_id)  # only do this once
            message = self.bot.message_cache.get(message_id)
            if message is None:
                message = await channel.fetch_message(message_id)
                self.bot.message_cache.put(message_id, message)
            label = self.get_label(message)
            if not label:
                return
            server = await ask_for_server(self.bot, message, label)

        elif not channel:
            # discord rapidly closes dm channels by desing
            # put private channels back into the bots cache and try again
            user = await self.bot.fetch_user(user_id)  # only do this once
            await user.create_dm()
            channel = self.bot.get_channel(channel_id)
            message = self.bot.message_cache.get(message_id)
            if message is None:
                message = await channel.fetch_message(message_id)
                self.bot.message_cache.put(message_id, message)
            label = self.get_label(message)
            if not label:
                return
            server = await ask_for_server(self.bot, message, label)
        else:
            return

        p = await Poll.load_from_db(self.bot, server.id, label)
        if not isinstance(p, Poll):
            return
        if not p.anonymous:
            # for anonymous polls we can't unvote because we need to hide reactions
            await p.unvote(user, emoji.name, message)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, data):
        # dont look at bot's own reactions
        #print('reaction_add data!ran', data)
        user_id = data.user_id
        if user_id == self.bot.user.id:
            return

        # get emoji symbol
        emoji = data.emoji
        # if emoji:
        #     emoji_name = emoji.name
        if not emoji:
            return
        # check if we can find a poll label
        message_id = data.message_id
        channel_id = data.channel_id
        channel = self.bot.get_channel(channel_id)
        #print('reaction_add data!channel', type(channel))
        if isinstance(channel, discord.TextChannel):
            #print('reactiontextchannel ran!')
            server = channel.guild
            #print('reactiontextchannel ran!server', server)
            # user = server.get_member(user_id)
            #print('reaction textchannel ran!', 'm_id', message_id)
            message = self.bot.message_cache.get(message_id)
            #print('reaction textchannel ran!message', message, 'm_id', message_id)
            #messagev2 = await channel.fetch_message(message_id)
            #labelv2 = self.get_label(messagev2)
            #print('reactiontextchannel ran!labelv2', labelv2)
            #print('reactiontextchannel ran!message', message)
            if message is None:
                #print('yes message is None!!')
                try:
                    message = await channel.fetch_message(message_id)
                except discord.errors.Forbidden:
                    # Ignore Missing Access error
                    return
                self.bot.message_cache.put(message_id, message)
            if message.author.id != self.bot.user.id:
                #print("ignore message", message_id)
                return
            label = self.get_label(message)
            #print('reactiontextchannel ran!label', label)
            if not label:
                return
        elif isinstance(channel, discord.Thread):
            #print('reactionThreadchannel ran!')
            server = channel.guild
            # user = server.get_member(user_id)
            message = self.bot.message_cache.get(message_id)
            if message is None:
                #print('yes message is None!!')
                try:
                    message = await channel.fetch_message(message_id)
                except discord.errors.Forbidden:
                    # Ignore Missing Access error
                    return
                self.bot.message_cache.put(message_id, message)
            if message.author.id != self.bot.user.id:
                #print("ignore message", message_id)
                return
            label = self.get_label(message)
            #print('reactionThreadchannel ran!label', label)
            if not label:
                return
        elif isinstance(channel, discord.DMChannel):
            #print('reactionDM ran!')
            user = await self.bot.fetch_user(user_id)  # only do this once
            message = self.bot.message_cache.get(message_id)
            if message is None:
                message = await channel.fetch_message(message_id)
                self.bot.message_cache.put(message_id, message)
            label = self.get_label(message)
            if not label:
                return
            server = await ask_for_server(self.bot, message, label)
        elif not channel:
            # discord rapidly closes dm channels by design
            # put private channels back into the bots cache and try again
            #print('reaction notchannel ran!')
            user = await self.bot.fetch_user(user_id)  # only do this once
            await user.create_dm()
            channel = self.bot.get_channel(channel_id)
            message = self.bot.message_cache.get(message_id)
            if message is None:
                message = await channel.fetch_message(message_id)
                self.bot.message_cache.put(message_id, message)
            label = self.get_label(message)
            if not label:
                return
            server = await ask_for_server(self.bot, message, label)
        else:
            #print('reaction else ran!')
            return

        p = await Poll.load_from_db(self.bot, server.id, label)
        #print('reaction getpoll ran!')
        if not isinstance(p, Poll):
            return
        # member = server.get_member(user_id)
        user = member = data.member
        # export
        if emoji.name == '📎':
            self.ignore_next_removed_reaction[str(message.id) + str(emoji)] = user_id
            self.bot.loop.create_task(message.remove_reaction(emoji, member))  # remove reaction

            # sending file
            file_name = await p.export()
            if file_name is not None:
                try:
                    await user.send('Sending you the requested export of "{}".'.format(p.short), file=discord.File(file_name))
                except discord.Forbidden:
                    config_result = await self.bot.db.config.find_one({'_id': str(server.id)})
                    if config_result and not config_result.get('error_mess') or config_result and config_result.get('error_mess') == 'True':
                        errormessage = traceback.format_exc(limit=0)
                        embederror = discord.Embed(title='Poll Reaction Error', color=discord.Color.red())
                        if errormessage.find("Cannot send messages to this user") >= 0:
                            embederror.add_field(name=f'Error type:', value='Error: can\'t send you a DM. please allow DM for this bot!', inline=False )
                            embederror.set_footer(text=f'From poll: {p.short} \nThis message will self-destruct in 1 min.')
                            await channel.send(f"<@{user.id}> Error!", embed=embederror, delete_after=60)
                        else:
                            print('error = unknown', traceback.format_exc())
                    else:
                        pass
            return

        # info

        elif emoji.name == '❔':
            self.ignore_next_removed_reaction[str(message.id) + str(emoji)] = user_id
            self.bot.loop.create_task(message.remove_reaction(emoji, member))  # remove reaction
            is_open = await p.is_open()
            embed = discord.Embed(title=f"Info for the {'CLOSED ' if not is_open else ''}poll \"{p.short}\"",
                                  description='', color=SETTINGS.color)
            embed.set_author(name=f" >> {p.short}", icon_url=SETTINGS.author_icon)

            # created by
            if (p.author is not None):
                created_by = await self.bot.member_cache.get(server, int(p.author.id))
                if created_by is None:
                    try:
                        created_by = await self.bot.fetch_user(int(p.author.id))
                    except:
                        created_by = "<Unknown User>"
                        pass 
            else:
                created_by = "<Deleted User>"
            # created_by = server.get_member(int(p.author.id))
            embed.add_field(name=f'Created by:', value=f'{created_by}',
                            inline=False)

            # vote rights
            vote_rights = p.has_required_role(member)
            embed.add_field(name=f'{"Can you vote?" if is_open else "Could you vote?"}',
                            value=f'{"✅" if vote_rights else "❎"}', inline=False)

            # edit rights
            edit_rights = False
            if p.author == None:
                if member.guild_permissions.manage_guild:
                    edit_rights = True
                else:
                    result = await self.bot.db.config.find_one({'_id': str(server.id)})
                    if result and result.get('admin_role') in [r.name for r in member.roles]:
                        edit_rights = True
            else:
                if str(member.id) == str(p.author.id):
                    edit_rights = True
                elif member.guild_permissions.manage_guild:
                    edit_rights = True
                else:
                    result = await self.bot.db.config.find_one({'_id': str(server.id)})
                    if result and result.get('admin_role') in [r.name for r in member.roles]:
                        edit_rights = True
            embed.add_field(name='Can you manage the poll?', value=f'{"✅" if edit_rights else "❎"}', inline=False)

            # choices
            user_votes = await p.load_votes_for_user(user.id)
            choices = 'You have not voted yet.' if vote_rights else 'You can\'t vote in this poll.'
            if user_votes and len(user_votes) > 0:
                choices = ', '.join([p.options_reaction[v.choice] for v in user_votes])
            embed.add_field(
                name=f'{"Your current votes (can be changed as long as the poll is open):" if is_open else "Your final votes:"}',
                value=choices, inline=False)

            # weight
            if vote_rights:
                weight = 1
                if len(p.weights_roles) > 0:
                    valid_weights = [p.weights_numbers[p.weights_roles.index(r)] for r in
                                     list(set([n.name for n in member.roles]).intersection(set(p.weights_roles)))]
                    if len(valid_weights) > 0:
                        weight = max(valid_weights)
            else:
                weight = 'You can\'t vote in this poll.'
            embed.add_field(name='Weight of your votes:', value=weight, inline=False)

            # time left
            deadline = p.get_duration_with_tz()
            if not is_open:
                time_left = 'This poll is closed.'
            elif deadline == 0:
                time_left = 'Until manually closed.'
            else:
                time_left = str(deadline - datetime.datetime.utcnow().replace(tzinfo=pytz.utc)).split('.', 2)[0]

            embed.add_field(name='Time left in the poll:', value=time_left, inline=False)
            #await user.send(embed=embed)
            try:
                await user.send(embed=embed)
            except discord.Forbidden:
                config_result = await self.bot.db.config.find_one({'_id': str(server.id)})
                if config_result and not config_result.get('error_mess') or config_result and config_result.get('error_mess') == 'True':
                    errormessage = traceback.format_exc(limit=0)
                    embederror = discord.Embed(title='Poll Reaction Error!', color=discord.Color.red())
                    if errormessage.find("Cannot send messages to this user") >= 0:
                        embederror.add_field(name=f'Error type:', value='Error: can\'t send you a DM. please allow DM for this bot!', inline=False )
                        embederror.set_footer(text=f'From poll: {p.short} \nThis message will self-destruct in 1 min.')
                        await channel.send(f"<@{user.id}> Error!", embed=embederror, delete_after=60)
                    else:
                        print('error = unknown', traceback.format_exc())
                else:
                    pass

            await p.load_full_votes()
            # await p.load_vote_counts()
            await p.load_unique_participants()
            # send current details of who currently voted for what
            if not p.anonymous and len(p.full_votes) > 0:
                msg = '--------------------------------------------\n' \
                      'VOTES\n' \
                      '--------------------------------------------\n'
                for i, o in enumerate(p.options_reaction):
                    if not p.hide_count or not p.open:
                        if not p.options_reaction_default and not p.options_reaction_emoji_only:
                            msg += AZ_EMOJIS[i] + " "
                        msg += "**" + o + ":**"
                    c = 0
                    for vote in p.full_votes:
                        # member = server.get_member(int(vote.user_id))
                        # member: discord.Member = await self.bot.fetch_user(int(vote.user_id))
                        member: discord.Member = await self.bot.member_cache.get(server, int(vote.user_id))
                        if member is None:
                            try:
                                member: discord.Member = await self.bot.fetch_user(int(vote.user_id))
                            except:
                                pass
                        if not member or vote.choice != i:
                            continue
                        c += 1
                        name = member.display_name
                        if not name:
                            name = member.name
                        if len(regex.findall(f"{name}", msg)) > 0 and p.hide_count and p.open:
                            name = " "
                        if not name:
                            name = "<Deleted User>"
                        msg += f'\n{name}'
                        if i in p.survey_flags:
                            msg += f': {vote.answer}'
                        if len(msg) > 1500:
                            await user.send(msg)
                            msg = ''
                    if c == 0 and (not p.hide_count or not p.open):
                        msg += '\nNo votes for this option yet.'
                    if not p.hide_count or not p.open:
                        msg += '\n\n'

                if len(msg) > 0:
                    await user.send(msg)
            elif (not p.open or not p.hide_count) and p.anonymous and len(p.survey_flags) > 0 and len(p.full_votes) > 0:
                msg = '--------------------------------------------\n' \
                      'Custom Answers (Anonymous)\n' \
                      '--------------------------------------------\n'
                has_answers = False
                for i, o in enumerate(p.options_reaction):
                    if i not in p.survey_flags:
                        continue
                    custom_answers = ''
                    for vote in p.full_votes:
                        if vote.choice == i:
                            has_answers = True
                            custom_answers += f'\n{vote.answer}'
                    if len(custom_answers) > 0:
                        if not p.options_reaction_emoji_only:
                            msg += AZ_EMOJIS[i] + " "
                        msg += "**" + o + ":**"
                        msg += custom_answers
                        msg += '\n\n'
                    if len(msg) > 1500:
                        await user.send(msg)
                        msg = ''
                if has_answers and len(msg) > 0:
                    await user.send(msg)
            return
        else:
            # Assume: User wants to vote with reaction
            # no rights, terminate function
            if not p.has_required_role(member):
                await message.remove_reaction(emoji, user)
                # await member.send(f'You are not allowed to vote in this poll. Only users with '
                #                   f'at least one of these roles can vote:\n{", ".join(p.roles)}')
                # return
                try:
                    await member.send(f'You are not allowed to vote in this poll. Only users with '
                                f'at least one of these roles can vote:\n{", ".join(p.roles)}')
                except discord.Forbidden:
                    config_result = await self.bot.db.config.find_one({'_id': str(server.id)})
                    if config_result and not config_result.get('error_mess') or config_result and config_result.get('error_mess') == 'True':
                        errormessage = traceback.format_exc(limit=0)
                        embederror = discord.Embed(title='Poll Reaction Error!', color=discord.Color.red())
                        if errormessage.find("Cannot send messages to this user") >= 0:
                            embederror.add_field(name=f'Error type:', value='Error: can\'t send you a DM. please allow DM for this bot!', inline=False )
                            embederror.set_footer(text=f'From poll: {p.short} \nThis message will self-destruct in 1 min.')
                            await channel.send(f"<@{user.id}> Error!", embed=embederror, delete_after=60)
                        else:
                            print('error = unknown', traceback.format_exc())
                    else:
                        pass
                return

            # check if we need to remove reactions (this will trigger on_reaction_remove)
            if not isinstance(channel, discord.DMChannel) and (p.anonymous or p.hide_count):
                # immediately remove reaction and to be safe, remove all reactions
                self.ignore_next_removed_reaction[str(message.id) + str(emoji)] = user_id
                await message.remove_reaction(emoji, user)

                # clean up all reactions (prevent lingering reactions)
                for rct in message.reactions:
                    if rct.count > 1:
                        async for user in rct.users():
                            if user == self.bot.user:
                                continue
                            self.ignore_next_removed_reaction[str(message.id) + str(rct.emoji)] = user_id
                            self.bot.loop.create_task(rct.remove(user))

            # order here is crucial since we can't determine if a reaction was removed by the bot or user
            # update database with vote
            await p.vote(member, emoji, message)


async def setup(bot):
    global logger
    logger = logging.getLogger('discord')
    await bot.add_cog(PollControls(bot))