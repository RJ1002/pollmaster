import asyncio
import logging
import datetime as dt

import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View

from essentials.multi_server import get_server_pre, ask_for_server
from essentials.settings import SETTINGS


class Help(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.pages = ['🏠', '🆕', '🔍', '🕹', '🛠', '❔', '💖']

    async def embed_list_reaction_handler(self, ctx, page, pre, msg=None):
        embed = self.get_help_embed(page, pre)
        if msg is None:
            msg = await ctx.followup.send(embed=embed)
            # add reactions
            for emoji in self.pages:
                await msg.add_reaction(emoji)
        else:
            await msg.edit(embed=embed)

        # wait for reactions (3 minutes)
        def check(rct, usr):
            return True if usr != self.bot.user and str(rct.emoji) in self.pages and rct.message.id == msg.id else False

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=300, check=check)
        except asyncio.TimeoutError:
            try:
                print('help menu deleted!')
                await msg.delete()
                await ctx.followup.delete()
            except discord.errors.NotFound:
                # message already deleted
                pass
            return None
        else:
            if isinstance(reaction.message.channel, discord.TextChannel) or isinstance(reaction.message.channel, discord.Thread):
                await reaction.message.remove_reaction(reaction.emoji, user)
            return reaction

    def get_help_embed(self, page, pre):

        title = f' RT Pollmaster Help - React with an emoji to learn more about a topic!'
        embed = discord.Embed(title='', description='', colour=SETTINGS.color)
        embed.set_author(name=title, icon_url=SETTINGS.author_icon)
        embed.set_footer(text='Use reactions to navigate the help. This message will self-destruct in 5 minutes.')



        if page == '🏠':
            embed.add_field(name='📣 Important Info!:',
                            value=f'⚠️**Issue!:** make sure you don''t have more then one wizard running!! stop/cancel the wizard before starting another one or it could cause issues in creating a poll.\n'
                                    f'Please join our [discord server](https://discord.gg/sjrDM6WES2) for support, info about Updates/changes to the bot, when outage/scheduled maintenance is happening, Beta testing, and more!!',
                            inline=False)
            # POLL CREATION SHORT
            embed.add_field(name='🆕 Making New Polls',
                            value=f'</quick:1102089006583382129> | </new:1102089006583382132> | </advanced:1102089006583382131> | </prepare:1102089006583382130> | </cmd:1102089006583382128> `<args>`\n'
                                  f'</quickslash:1159928841758843035> | </newslash:1159928841758843039> | </advancedslash:1159928841758843037> | </prepareslash:1159928841758843036>',
                            inline=False)
            # embed.add_field(name='Commands', value=f'`{pre}quick` | `{pre}new` | `{pre}prepared`', inline=False)
            # embed.add_field(name='Arguments', value=f'Arguments: `<poll question>` (optional)', inline=False)
            # embed.add_field(name='Examples', value=f'Examples: `{pre}new` | `{pre}quick What is the greenest color?`',
            #                 inline=False)

            ## POLL CONTROLS
            embed.add_field(name='🔍 Show Polls',
                            value=f'</show:1102089006335922265> | `/show <label>` | `/show <category>`', inline=False)
            # embed.add_field(name='Command', value=f'`{pre}show (label)`', inline=False)
            # embed.add_field(name='Arguments', value=f'Arguments: `open` (default) | `closed` | `prepared` | '
            #                                         f'`<poll_label>` (optional)', inline=False)
            # embed.add_field(name='Examples', value=f'Examples: `{pre}show` | `{pre}show closed` | `{pre}show mascot`',
            #                 inline=False)

            # POLL CONTROLS
            embed.add_field(name='🕹 Poll Controls',
                            value=f'</copy:1102089006335922263> | </close:1102089006335922262> | </export:1102089006335922264> | </delete:1102089006335922261> | </activate:1102089006335922259>',
                            inline=False)
            # embed.add_field(name='Commands', value=f'`{pre}close` | `{pre}export` | `{pre}delete` | `{pre}activate` ',
            #                 inline=False)
            # embed.add_field(name='Arguments', value=f'Arguments: <poll_label> (required)', inline=False)
            # embed.add_field(name='Examples', value=f'Examples: `{pre}close mascot` | `{pre}export proposal`',
            #                 inline=False)

            # POLL CONTROLS
            embed.add_field(name='🛠 Configuration',
                            value=f'</userrole:1102089006335922258> `[role]` | </adminrole:1102089006335922257> `[role]` | </prefix:1102089006335922256> `<new_prefix>` | </settings:1196482521513328722>',
                            inline=False
                            )

            # DEBUGGING
            embed.add_field(name='❔ Debugging',
                            value=f'`@debug`\n '
                                  f'</debug:1102089006583382134> ',
                            inline=False
                            )
            # ABOUT
            embed.add_field(name='💖 About RT Pollmaster',
                            value='More infos about RT Pollmaster, the developer, where to go for further help and how you can support us.',
                            inline=False)
            # LINKS                
            embed.add_field(name=':paperclip: Useful Links',
                            value='[Support Server](https://discord.gg/sjrDM6WES2), [Top.gg page](https://top.gg/bot/753217458029985852), [Donation page](https://ko-fi.com/rtpollmaster)',
                            inline=False)

        elif page == '🆕':
            embed.add_field(name='🆕 Making New Polls',
                            value='There are four ways to create a new poll. For all the commands you can either just '
                                  'type the command or type the command followed by the question to skip the first step.'
                                  'Your Members need the <admin> or <user> role to use these commands. '
                                  'More on user rights in 🛠 Configuration.\n'
                                  f'**Notice!:** for commands `/quickslash` and `/newslash` and `/advancedslash` and `/prepareslash` \n They have the same options as there normal commands but each option is in the slash command.\n'
                                  '⚠️**Issue!:** make sure you don''t have more then one wizard running!! stop/cancel the wizard before starting another one or it could cause issues in creating a poll.\n(your allowed more then one wizard if it from a different account)',
                            inline=False)
            embed.add_field(name=f'🔹 **Quick Poll:** </quick:1102089006583382129> or </quickslash:1159928841758843035>',
                            value='If you just need a quick poll, this is the way to go. All you have to specify is the '
                                  'question and your answers; the rest will be set to default values.',
                            inline=False)
            embed.add_field(name=f'🔹 **Basic Poll:** </new:1102089006583382132> or </newslash:1159928841758843039>',
                            value='This command gives control over the most common settings. A step by step wizard will guide '
                                  'you through the process and you can specify options such as Multiple Choice, '
                                  'Anonymous Voting and Deadline.',
                            inline=False)
            embed.add_field(name=f'🔹 **Advanced Poll:** </advanced:1102089006583382131> or </advancedslash:1159928841758843037>',
                            value='This command gives you full control over your poll. A step by step wizard will guide '
                                  'you through the process and you can specify additional options such as Hide Vote Count, '
                                  'Role Restrictions, Role Weights or Custom Write-In Answers (Survey Flags).',
                            inline=False)
            embed.add_field(name=f'🔹 **Prepare and Schedule:** </prepare:1102089006583382130> or </prepareslash:1159928841758843036>',
                            value=f'Similar to `{pre}advanced`, this gives you all the options. But additionally, the poll will '
                                  'be set to \'inactive\'. You can specify if the poll should activate at a certain time '
                                  f'and/or if you would like to manually `{pre}activate` it. '
                                  'Perfect if you are preparing for a team meeting!',
                            inline=False)
            embed.add_field(name=f'🔹 **-Advanced- Commandline:** </cmd:1102089006583382128> `<arguments>`',
                            value=f'For the full syntax type `{pre}cmd help`\n'
                                  f'Similar to version 1 of the bot, with this command you can create a poll in one message. '
                                  f'Pass all the options you need via command line arguments, the rest will be set to '
                                  f'default values. The wizard will step in for invalid arguments.\n'
                                  f'Example: `{pre}cmd -q "Which colors?" -l colors -o "green, blue, red" -h -a`',
                            inline=False)


        elif page == '🔍':
            embed.add_field(name='🔍 Show Polls',
                            value='All users can display and list polls, with the exception of prepared polls. '
                                  'Voting is done simply by using the reactions below the poll.',
                            inline=False)
            embed.add_field(name=f'🔹 **Show a Poll:** </show:1102089006335922265> `<poll_label>`',
                            value='This command will refresh and display a poll. The votes in the message will always '
                                  'be up to date and accurate. The number of reactions can be different for a number '
                                  'of reasons and you can safely disregard them.',
                            inline=False)
            embed.add_field(name=f'🔹 **List Polls:** `/show <> | open | closed | prepared`',
                            value=f'If you just type `{pre}show` without an argument it will default to `{pre}show open`.'
                                  'These commands will print a list of open, closed or prepared polls that exist on '
                                  'the server. The first word in bold is the label of the poll and after the colon, '
                                  'you can read the question. These lists are paginated and you can use the arrow '
                                  'reactions to navigate larger lists.',
                            inline=False)
        elif page == '🕹':
            embed.add_field(name='🕹 Poll Controls',
                            value='All these commands except copy can only be used by an <admin> or by the author of the poll. '
                                  'Go to 🛠 Configuration for more info on the permissions.',
                            inline=False)
            embed.add_field(name=f'🔹 **Copy** </copy:1102089006335922263> `<poll_label>`',
                            value='This will give you a cmd string that you can post into any channel to create a copy'
                                  'of the specified poll. It will increment the label and depending on the settings, '
                                  'you might need to add missing information like a new deadline. '
                                  f'\nFor more info, see: `{pre}cmd help`.',
                            inline=False)
            embed.add_field(name=f'🔹 **Close** or </close:1102089006335922262> `<poll_label>`',
                            value='Polls will close automatically when their deadline is reached. But you can always '
                                  'close them manually by using this command. A closed poll will lock in the votes so '
                                  'users can no longer change, add or remove votes. Once closed, you can export a poll.',
                            inline=False)
            embed.add_field(name=f'🔹 **Delete** or </delete:1102089006335922261> `<poll_label>`',
                            value='This will *permanently and irreversibly* delete a poll from the database. '
                                  'Once done, the label is freed up and can be assigned again.',
                            inline=False)
            embed.add_field(name=f'🔹 **Export** or </export:1102089006335922264> `<poll_label>`',
                            value='You can use this command or react with 📎 to a closed poll to generate a report. '
                                  'The report will then be sent to you in discord via the bot. This utf8-textfile '
                                  '(make sure to open it in an utf8-ready editor) will contain all the infos about the '
                                  'poll, including a detailed list of participants and their votes (just a list of names '
                                  'for anonymous polls).',
                            inline=False)
            embed.add_field(name=f'🔹 **Activate** or </activate:1102089006335922259> `<poll_label>`',
                            value=f'To see how you can prepare inactive polls read the `{pre}prepare` command under Making '
                                  'New Polls. This command is used to manually activate a prepared poll.',
                            inline=False)

        elif page == '🛠':
            embed.add_field(name='🛠 Configuration',
                            value='To run any of these commands you need the **\"Manage Server\"** permisson.',
                            inline=False)
            embed.add_field(name=f'🔹 **Poll Admins** </adminrole:1102089006335922257> `<role name> (optional)`',
                            value='This gives the rights to create polls and to control ALL polls on the server. '
                                  f'To see the current role for poll admin, run the command without an argument: `{pre}adminrole`\n'
                                  'If you want to change the admin role to any other role, use the name of the new role '
                                  f'as the argument: `{pre}adminrole moderators`',
                            inline=False)
            embed.add_field(name=f'🔹 **Poll Users** </userrole:1102089006335922258> `<role name> (optional)`',
                            value='Everything here is identical to the admin role, except that Poll Users can only '
                                  'control the polls which were created by themselves.',
                            inline=False)
            embed.add_field(name=f'🔹 **Change Prefix** or </prefix:1102089006335922256> `<new_prefix>`',
                            value='This will change the bot prefix for your server. If you want to use a trailing '
                                  'whitespace, use "\w" instead of " " (discord deletes trailing whitespaces).',
                            inline=False)
            embed.add_field(name=f'🔹 **To change settings** </settings:1196482521513328722>',
                            value="This will either change the settings for the poll closed message or the error message\n"
                                   "The poll closed setting is to disabled the poll closed message that is send when a poll is schedule to be closed\n"
                                   "The error message setting is to disabled the message that is send if the bot can't DM a user.",
                            inline=False)

        elif page == '❔':
            embed.add_field(name='❔ Debugging',
                            value='These commands are independent of your server prefix and serve to debug the bot.',
                            inline=False)
            embed.add_field(name=f'🔹 **Debug:** `@debug` or </debug:1102089006583382134>',
                            value='This command will check the required permissions in the channel it is used and'
                                  'generate a short report with suggestions on your next actions.'
                                  'If you are stuck, please visit the support discord server.',
                            inline=False)
            # embed.add_field(name=f'🔹 **Mention:** `@mention` | `@mention prefix` or </mention:1102089006583382135> `<tag>`',
            #                 value='This is a prefix independent command to retrieve your prefix in case you changed '
            #                       'and forgot it. More `@mention` tags might be added in the future.',
            #                 inline=False)

        elif page == '💖':
            embed.add_field(name='💖 RT Pollmaster 💖',
                            value='If you enjoy the bot, you can show your appreciation by giving him an upvote on top.gg.',
                            inline=False)
            embed.add_field(name='🔹 **Developer**',
                            value='developed by RJGamer1002 (<@183940132129210369>)',
                            inline=False)
            embed.add_field(name='🔹 **Support**',
                            value='You can support RT Pollmaster by sending an upvote his way or by writing a review '
                                  'on the top.gg page:\n https://top.gg/bot/753217458029985852'
                                  '\nYou can also donate here: https://ko-fi.com/rtpollmaster',
                            inline=False)
            embed.add_field(name='🔹 **Support Server**',
                            value='If you need help with RT Pollmaster, want to try him out or would like to give feedback '
                                  'to the developer, feel free to join the support server: https://discord.gg/sjrDM6WES2',
                            inline=False)
            embed.add_field(name='🔹 **Github**',
                            value='The full python source code is on my Github: https://github.com/RJ1002/pollmaster',
                            inline=False)
            embed.add_field(name='**Thanks for using RT Pollmaster!** 💗', value='RJGamer1002', inline=False)
        else:
            return None

        return embed

    # @commands.hybrid_command(name="pmhelp",description="Display commands")

    @app_commands.command(name="help", description="Display commands")
    async def pmhelp(self, ctx):
        server = await ask_for_server(self.bot, ctx)
        if not server:
            return
        await ctx.response.defer(thinking=True)

        if not (isinstance(ctx.channel, discord.TextChannel) or isinstance(ctx.channel, discord.Thread)):
            await ctx.followup.send("`help` can only be used in a server text channel.")
            return
        permissions = ctx.channel.permissions_for(server.me)
        if not permissions.embed_links or not permissions.manage_messages or not permissions.add_reactions or not permissions.read_message_history:
            await ctx.followup.send("Error: Missing permissions. Type \"/debug.\"")
            return
        
        guild = ctx.guild
        if not guild:
            await ctx.followup.send("Could not determine your server. Run the command in a server text channel.")
            return
        print('help menu started!')
        pre = await get_server_pre(self.bot, server)
        rct = 1
        while rct is not None:
            if rct == 1:
                page = '🏠'
                msg = None
            else:
                page = rct.emoji
                msg = rct.message
            rct = await self.embed_list_reaction_handler(ctx, page, pre, msg)
        else:
            pass
            
    # @mention and @debug commands
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if message.content.startswith(f"<@{self.bot.user.id}>"):
            print(message.content)
            print(self.bot.user.name)
            try:
                print(message.guild.id)
                print(message.author.id)
            except:
                print("none")

            # if message.content.startswith(f"<@{self.bot.user.id}> mention"):
            #     channel = message.channel
            #     if not isinstance(channel, discord.TextChannel):
            #         await channel.send("@mention can only be used in a server text channel.")
            #         return

            #     guild = message.guild
            #     if not guild:
            #         await channel.send("Could not determine your server.")
            #         return

            #     if message.content == f"<@{self.bot.user.id}> mention":
            #         await channel.send("The following mention tags are available:\n🔹 mention prefix")
            #         return

            #     try:
            #         tags = message.content.split()
            #         tag = tags[len(tags)-1].lower()
            #     except IndexError:
            #         await channel.send(f"Wrong formatting. Type \"@{self.bot.user.name} mention\" or "
            #                            f"\"@{self.bot.user.name} mention <tag>\".")
            #         return

            #     if tag == "prefix":
            #         pre = await get_server_pre(self.bot, guild)
            #         # await channel.send(f'The prefix for this server/channel is: \n {pre} \n To change it type: \n'
                    #                    f'{pre}prefix <new_prefix>')
            #         await channel.send(pre)
            #     else:
            #         await channel.send(f'Tag "{tag}" not found. Type `@{self.bot.user.name} mention` for a list of tags.')
            if message.content.startswith(f"<@{self.bot.user.id}> debug"):
                channel = message.channel
                if not isinstance(channel, discord.TextChannel):
                    await channel.send("`debug` can only be used in a server text channel.")
                    return

                guild = message.guild
                if not guild:
                    await channel.send("Could not determine your server. Run the command in a server text channel.")
                    return

                status_msg = ''
                setup_correct = True

                # check send message permissions
                permissions = channel.permissions_for(guild.me)
                if not permissions.send_messages:
                    await message.author.send(f'I don\'t have permission to send text messages in channel "{channel}" '
                                              f'on server "{guild}"')
                    return

                status_msg += ' ✅ Sending text messages\n'

                # check embed link permissions
                if permissions.embed_links:
                    status_msg += '✅ Sending embedded messages\n'
                else:
                    status_msg += '❗ Sending embedded messages. I need permissions to embed links!\n'
                    setup_correct = False

                # check manage messages
                if permissions.manage_messages:
                    status_msg += '✅ Deleting messages and reactions\n'
                else:
                    status_msg += '❗ Deleting messages and reactions. I need the manage messages permission!\n'
                    setup_correct = False

                # check adding reactions
                if permissions.add_reactions:
                    status_msg += '✅ Adding reactions\n'
                else:
                    status_msg += '❗ Adding reactions. I need the add reactions permission!\n'
                    setup_correct = False

                # read message history
                if permissions.read_message_history:
                    status_msg += '✅ Reading message history\n'
                else:
                    status_msg += '❗ Reading message history. ' \
                                  'I need to be able to read past messages in this channel!\n'
                    setup_correct = False

                if setup_correct:
                    status_msg += 'No action required. As far as i can see, your permissions are set up correctly ' \
                                  'for this channel. \n' \
                                  'If the bot does not work, feel free to join the support discord server.'
                else:
                    status_msg += 'Please try to fix the issues above. \nIf you are still having problems, ' \
                                  'visit the support discord server.'

                await channel.send(status_msg)

    @app_commands.command(name="debug", description="run debug")
    async def pmdebug(self, ctx):
        print("debug command")
        print(self.bot.user.name)
        await ctx.response.defer(thinking=True)
        if not (isinstance(ctx.channel, discord.TextChannel) or isinstance(ctx.channel, discord.Thread) or isinstance(ctx.channel, discord.DMChannel)):
            await ctx.followup.send("`debug` can only be used in a server text channel.")
            return

        guild = ctx.guild
        if not guild:
            await ctx.followup.send("Could not determine your server. Run the command in a server text channel.")
            return

        status_msg = ''
        setup_correct = True
        # check send message permissions
        permissions = ctx.channel.permissions_for(guild.me)
        if permissions.send_messages:
            status_msg += ' ✅ Sending text messages\n'
        else:
            status_msg += ' ❗ Sending text messages. I need send message permission!\n'
            setup_correct = False

        # check embed link permissions
        if permissions.embed_links:
            status_msg += '✅ Sending embedded messages\n'
        else:
            status_msg += '❗ Sending embedded messages. I need permissions to embed links!\n'
            setup_correct = False

        # check manage messages
        if permissions.manage_messages:
            status_msg += '✅ Deleting messages and reactions\n'
        else:
            status_msg += '❗ Deleting messages and reactions. I need the manage messages permission!\n'
            setup_correct = False

        # check adding reactions
        if permissions.add_reactions:
            status_msg += '✅ Adding reactions\n'
        else:
            status_msg += '❗ Adding reactions. I need the add reactions permission!\n'
            setup_correct = False

        # read message history
        if permissions.read_message_history:
            status_msg += '✅ Reading message history\n'
        else:
            status_msg += '❗ Reading message history. ' \
                          'I need to be able to read past messages in this channel!\n'
            setup_correct = False

        if setup_correct:
            status_msg += 'No action required. As far as i can see, your permissions are set up correctly ' \
                          'for this channel. \n' \
                          'If the bot does not work, feel free to join the support discord server.'
        else:
            status_msg += 'Please try to fix the issues above. \nIf you are still having problems, ' \
                          'visit the support discord server.'
        await ctx.followup.send(status_msg)
    # @app_commands.command(name="mention", description="run mention")
    # @app_commands.describe(
    #     tag='options: prefix',
    # )
    # async def pmmention(self, ctx, *, tag: str = None):
    #     if not isinstance(ctx.channel, discord.TextChannel):
    #         await ctx.response.send_message("`/mention` can only be used in a server text channel.", delete_after=60)
    #         return

    #     guild = ctx.guild
    #     if not guild:
    #         await ctx.response.send_message("Could not determine your server.", delete_after=60)
    #         return
    #     if tag == "prefix":
    #         pre = await get_server_pre(self.bot, guild)
    #         await ctx.response.send_message(f'The prefix for this server/channel is: \n {pre} \n To change it type: \n'
    #                             f'{pre}prefix <new_prefix>', delete_after=60)
    #         #await ctx.response.send_message(pre)
    #     elif tag == None:
    #         await ctx.response.send_message("The following mention tags are available:\n🔹 prefix", delete_after=60)
    #     else:
    #         await ctx.response.send_message(f'Tag "{tag}" not found. Type `/mention` for a list of tags.', delete_after=60)
    @app_commands.command(name="ping", description="send a ping to bot")
    async def pmping(self, ctx):
        if not (isinstance(ctx.channel, discord.TextChannel) or isinstance(ctx.channel, discord.Thread)):
            await ctx.response.send_message("`/ping` can only be used in a server text channel.")
            return
        guild = ctx.guild
        if not guild:
            await ctx.response.send_message("Could not determine your server. Run the command in a server text channel.")
            return
        else:
            await ctx.response.send_message(f'Pong! In {round(ctx.client.latency * 1000)}ms')
    

async def setup(bot):
    global logger
    logger = logging.getLogger('discord')
    await bot.add_cog(Help(bot))
