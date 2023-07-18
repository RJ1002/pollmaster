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
        self.pages = ['🏠', '🆕', '❓', '🔍', '🕹', '🛠', '❔', '💖']

    async def embed_list_reaction_handler(self, ctx, page, pre, msg=None):
        embed = self.get_help_embed(page, pre)
        if msg is None:
            msg = await ctx.send(embed=embed)
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
                await msg.delete()
                await ctx.message.delete()
            except discord.errors.NotFound:
                # message already deleted
                pass
            return None
        else:
            if isinstance(reaction.message.channel, discord.TextChannel):
                await reaction.message.remove_reaction(reaction.emoji, user)
            return reaction

    def get_help_embed(self, page, pre):

        title = f' RT Pollmaster Help - React with an emoji to learn more about a topic!'
        embed = discord.Embed(title='', description='', colour=SETTINGS.color)
        embed.set_author(name=title, icon_url=SETTINGS.author_icon)
        embed.set_footer(text='Use reactions to navigate the help. This message will self-destruct in 5 minutes.')

        #survey_flags message
        text = ("**Which options should ask the user for a custom answer?**\n"
                                        "Type `0` to skip survey options.\n"
                                        "If you want multiple survey options, separate the numbers with a comma.\n"
                                        "\n"
                                        "`0 - None (classic poll)`\n"
                                        )
        #for i, option in enumerate(self.options_reaction):
        #    text += f'`{i + 1} - {option}`\n'
        text += ("\n"
                 "If the user votes for one of these options, the bot will PM them and ask them to provide a text "
                 "input. You can use this to do surveys or to gather feedback for example.\n")
        
        text_roles = ("**Choose which roles are allowed to vote.**\n"
                    "Type `0`, `all` or `everyone` to have no restrictions.\n"
                    "If you want multiple roles to be able to vote, separate the numbers with a comma.\n")
        text_roles += f'\n`{0} - no restrictions`'

        #for i, role in enumerate([r.name for r in self.server.roles]):
        #        text += f'\n`{i+1} - {role}`'
        text_roles += ("\n"
                     "\n"
                     " Example: `2, 3` \n")
        
        text_roles = ("**Choose which roles are allowed to vote.**\n"
                    "Type `0`, `all` or `everyone` to have no restrictions.\n"
                    "Type out the role names, separated by a comma, to restrict voting to specific roles:\n"
                    "`moderators, Editors, vips` (hint: role names are case sensitive!)\n")

        if page == '🏠':
            # POLL CREATION SHORT
            embed.add_field(name='🆕 Making New Polls',
                            value=f'`{pre}quick` | `{pre}new` | `{pre}advanced` | `{pre}prepare` | `{pre}cmd <args>`\n'
                                  f'`/quick` | `/new` | `/advanced` | `/prepare` | `/cmd <args>`',
                            inline=False)
            # embed.add_field(name='Commands', value=f'`{pre}quick` | `{pre}new` | `{pre}prepared`', inline=False)
            # embed.add_field(name='Arguments', value=f'Arguments: `<poll question>` (optional)', inline=False)
            # embed.add_field(name='Examples', value=f'Examples: `{pre}new` | `{pre}quick What is the greenest color?`',
            #                 inline=False)
            # OPTION  what each option does
            embed.add_field(name='❓ Options',
                            value=f'The list of what each option does',
                            inline=False)

            ## POLL CONTROLS
            embed.add_field(name='🔍 Show Polls',
                            value=f'`{pre}show` | `{pre}show <label>` | `{pre}show <category>`\n'
                                  f'`/show` | `/show <label>` | `/show <category>`', inline=False)
            # embed.add_field(name='Command', value=f'`{pre}show (label)`', inline=False)
            # embed.add_field(name='Arguments', value=f'Arguments: `open` (default) | `closed` | `prepared` | '
            #                                         f'`<poll_label>` (optional)', inline=False)
            # embed.add_field(name='Examples', value=f'Examples: `{pre}show` | `{pre}show closed` | `{pre}show mascot`',
            #                 inline=False)

            # POLL CONTROLS
            embed.add_field(name='🕹 Poll Controls',
                            value=f'`{pre}copy` | `{pre}close` | `{pre}export` | `{pre}delete` | `{pre}activate`\n '
                                  f'`/copy` | `/close` | `/export` | `/delete` | `/activate` ',
                            inline=False)
            # embed.add_field(name='Commands', value=f'`{pre}close` | `{pre}export` | `{pre}delete` | `{pre}activate` ',
            #                 inline=False)
            # embed.add_field(name='Arguments', value=f'Arguments: <poll_label> (required)', inline=False)
            # embed.add_field(name='Examples', value=f'Examples: `{pre}close mascot` | `{pre}export proposal`',
            #                 inline=False)

            # POLL CONTROLS
            embed.add_field(name='🛠 Configuration',
                            value=f'`{pre}userrole [role]` | `{pre}adminrole [role]` | `{pre}prefix <new_prefix>`\n '
                                  f'`/userrole [role]` | `/adminrole [role]` | `/prefix <new_prefix>` ',
                            inline=False
                            )

            # DEBUGGING
            embed.add_field(name='❔ Debugging',
                            value=f'`@debug` | `@mention` | `@mention <tag>`\n '
                                  f'`/debug` | `/mention` | `/mention <tag>` ',
                            inline=False
                            )
            # ABOUT
            embed.add_field(name='💖 About RT Pollmaster',
                            value='More infos about Pollmaster, the developer, where to go for further help and how you can support us.',
                            inline=False)

        elif page == '🆕':
            embed.add_field(name='🆕 Making New Polls',
                            value='There are four ways to create a new poll. For all the commands you can either just '
                                  'type the command or type the command followed by the question to skip the first step.'
                                  'Your Members need the <admin> or <user> role to use these commands. '
                                  'More on user rights in 🛠 Configuration.',
                            inline=False)
            embed.add_field(name=f'🔹 **Quick Poll:** `{pre}quick` or `/quick`',
                            value='If you just need a quick poll, this is the way to go. All you have to specify is the '
                                  'question and your answers; the rest will be set to default values.',
                            inline=False)
            embed.add_field(name=f'🔹 **Basic Poll:** `{pre}new` or `/new`',
                            value='This command gives control over the most common settings. A step by step wizard will guide '
                                  'you through the process and you can specify options such as Multiple Choice, '
                                  'Anonymous Voting and Deadline.',
                            inline=False)
            embed.add_field(name=f'🔹 **Advanced Poll:** `{pre}advanced` or `/advanced`',
                            value='This command gives you full control over your poll. A step by step wizard will guide '
                                  'you through the process and you can specify additional options such as Hide Vote Count, '
                                  'Role Restrictions, Role Weights or Custom Write-In Answers (Survey Flags).',
                            inline=False)
            embed.add_field(name=f'🔹 **Prepare and Schedule:** `{pre}prepare` or `/prepare`',
                            value=f'Similar to `{pre}advanced`, this gives you all the options. But additionally, the poll will '
                                  'be set to \'inactive\'. You can specify if the poll should activate at a certain time '
                                  f'and/or if you would like to manually `{pre}activate` it. '
                                  'Perfect if you are preparing for a team meeting!',
                            inline=False)
            embed.add_field(name=f'🔹 **-Advanced- Commandline:** `{pre}cmd <arguments>` or `/cmd <arguments>`',
                            value=f'For the full syntax type `{pre}cmd help`\n'
                                  f'Similar to version 1 of the bot, with this command you can create a poll in one message. '
                                  f'Pass all the options you need via command line arguments, the rest will be set to '
                                  f'default values. The wizard will step in for invalid arguments.\n'
                                  f'Example: `{pre}cmd -q "Which colors?" -l colors -o "green, blue, red" -h -a`',
                            inline=False)

                    
        elif page == '❓':
            embed.add_field(name='❓ Options',
                            value='This will be the list of options that each poll will be asking\n'
                                  'Your Members need the <admin> or <user> role to use these.\n'
                                  'More on user rights in 🛠 Configuration.',
                            inline=False)
            embed.add_field(name=f'🔹 **name:** `Set the Question / Name of the Poll.`',
                            value='**What is the question of your poll?**\n'
                                    'Try to be descriptive without writing more than one sentence.\n'
                                    'Error message you might get: **Keep the poll question between 3 and 400 valid characters**',
                            inline=False)
            embed.add_field(name=f'🔹 **short:** `Set the label of the Poll.`',
                            value='**Now type a unique one word identifier, a label, for your poll.**\n'
                                    'This label will be used to refer to the poll. Keep it short and significant.\n'
                                  'Error message you might get: **Only one word between 2 and 25 valid characters!** \n'
                                  '**Can\'t use reserved words (open, closed, prepared) as label!**\n **The label `{reply}` is not unique on this server. Choose a different one!**',
                            inline=False)
            embed.add_field(name=f'🔹 **preparation:** `Set the preparation conditions for the Poll.`',
                            value='This poll will be created inactive. You can either schedule activation at a certain date or activate \n'
                                  'it manually. **Type `0` to activate it manually or tell me when you want to activate it** by \n'
                                  'typing an absolute or relative date. You can specify a timezone if you want.\n'
                                  'Examples: `in 2 days`, `next week CET`, `may 3rd 2019`, `9.11.2019 9pm EST`\n'
                                  'Error message you might get: **Specify the activation time in a format i can understand.** \n **Type Error.**\n **{e.date.strftime("%d-%b-%Y %H:%M")} is in the past.**',
                            inline=False)
            embed.add_field(name=f'🔹 **anonymous:** `Determine if poll is anonymous.`',
                            value=f'you need to decide: **Do you want your poll to be anonymous?**\n'
                                  '\n'
                                  f'`0 - No`\n'
                                  '`1  - Yes`\n'
                                  '\n'
                                  'An anonymous poll has the following effects:\n'
                                  '🔹 You will never see who voted for which option\n'
                                  '🔹 Once the poll is closed, you will see who participated (but not their choice)\n'
                                  'Error message you might get: **You can only answer with `yes` | `1` or `no` | `0`!**',
                            inline=False)
            embed.add_field(name=f'🔹 **options_reaction:** `Set the answers / options of the Poll.`',
                            value=f'**Choose the options/answers for your poll.**\n'
                                  f'Either chose a preset of options or type your own options, separated by commas.\n'
                                  f'\n'
                                  f'**1** - :white_check_mark: :negative_squared_cross_mark:\n'
                                  f'**2** - :thumbsup: :zipper_mouth: :thumbsdown:\n'
                                  f'**3** - :heart_eyes: :thumbsup: :zipper_mouth:  :thumbsdown: :nauseated_face:\n'
                                  f'**4** - in favour, against, abstaining\n'
                                  f'\n'
                                  f'Example for custom options:\n'
                                  f'**apple juice, banana ice cream, kiwi slices** \n'
                                  f'Error message you might get: **Invalid entry. Type `1`, `2`, `3` or `4` or a comma separated list of up to 18 options.**\n **You need more than 1 and less than 19 options! Type them in a comma separated list.**',
                            inline=False)
            embed.add_field(name=f'🔹 **survey_flags:** `Decide which Options will ask for user input.`',
                            value=text,
                            inline=False)
            
            embed.add_field(name=f'🔹 **multiple_choice:** `Determine if poll is multiple choice.`',
                            value=f'**How many options should the voters be able choose?**\n'
                                  '\n'
                                  f'`0 - No Limit: Multiple Choice`\n'
                                  '`1  - Single Choice`\n'
                                  '`2+  - Specify exactly how many Choices`\n'
                                  '\n'
                                  'If the maximum choices are reached for a voter, they have to unvote an option before being able to '
                                  'vote for a different one.'
                                  'Error message you might get: **Invalid Input** \n **Enter a positive number** \n **You can\'t have more choices than options.**',
                            inline=False)
            embed.add_field(name=f'🔹 **hide_vote_count:** `Determine the live vote count is hidden or shown.`',
                            value=f'**Do you want to hide the live vote count?**\n'
                                  '\n'
                                  f'`0 - No, show it (Default)`\n'
                                  '`1  - Yes, hide it`\n'
                                  '\n'
                                  'You will still be able to see the vote count once the poll is closed. This settings will just hide '
                                  'the vote count while the poll is active.'
                                  'Error message you might get: **You can only answer with `yes` | `1` or `no` | `0`!**',
                            inline=False)
            embed.add_field(name=f'🔹 **roles:** `Set role restrictions for the Poll.`',
                            value=text_roles,
                            inline=False)
            embed.add_field(name=f'🔹 **weights:** `Set role weights for the poll.`',
                            value=f'**Weights allow you to give certain roles more or less effective votes.**\n'
                                  '**Type `0` or `none` if you don\'t need any weights.**\n'
                                  f'A weight for the role `moderator` of `2` for example will automatically count the votes of all the moderators twice.\n'
                                  'To assign weights type the role, followed by a colon, followed by the weight like this:\n'
                                  '`moderator: 2, newbie: 0.5`'
                                  'Error message you might get: **Can\'t read this input.**\n **Expected roles and weights to be separated by {e.separator}**\n **Invalid role found: {e.roles}**\n **Weights must be numbers.**\n **Not every role has a weight assigned.**',
                            inline=False)
            embed.add_field(name=f'🔹 **duration:** `Set the duration /deadline for the Poll.`',
                            value=f'**When should the poll be closed?**\n'
                                  'If you want the poll to last indefinitely (until you close it), type `0`.\n'
                                  f'Otherwise tell me when the poll should close in relative or absolute terms. \n'
                                  'You can specify a timezone if you want.\n'
                                  '\n'
                                  'Examples: `in 6 hours` or `next week CET` or `aug 15th 5:10` or `15.8.2019 11pm EST`\n'
                                  'Error message you might get: **Specify the deadline in a format I can understand.**\n **Type Error.**\n **{e.date.strftime("%d-%b-%Y %H:%M")} is in the past.**',
                            inline=False)

        elif page == '🔍':
            embed.add_field(name='🔍 Show Polls',
                            value='All users can display and list polls, with the exception of prepared polls. '
                                  'Voting is done simply by using the reactions below the poll.',
                            inline=False)
            embed.add_field(name=f'🔹 **Show a Poll:** `{pre}show <poll_label>` or `/show <poll_label>`',
                            value='This command will refresh and display a poll. The votes in the message will always '
                                  'be up to date and accurate. The number of reactions can be different for a number '
                                  'of reasons and you can safely disregard them.',
                            inline=False)
            embed.add_field(name=f'🔹 **List Polls:** `{pre}show <> | open | closed | prepared` or `/show <> | open | closed | prepared`',
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
            embed.add_field(name=f'🔹 **Copy** `{pre}copy <poll_label>` or `/copy <poll_label>`',
                            value='This will give you a cmd string that you can post into any channel to create a copy'
                                  'of the specified poll. It will increment the label and depending on the settings, '
                                  'you might need to add missing information like a new deadline. '
                                  f'\nFor more info, see: `{pre}cmd help`.',
                            inline=False)
            embed.add_field(name=f'🔹 **Close** `{pre}close <poll_label>` or `/close <poll_label>`',
                            value='Polls will close automatically when their deadline is reached. But you can always '
                                  'close them manually by using this command. A closed poll will lock in the votes so '
                                  'users can no longer change, add or remove votes. Once closed, you can export a poll.',
                            inline=False)
            embed.add_field(name=f'🔹 **Delete** `{pre}delete <poll_label>` or `/delete <poll_label>`',
                            value='This will *permanently and irreversibly* delete a poll from the database. '
                                  'Once done, the label is freed up and can be assigned again.',
                            inline=False)
            embed.add_field(name=f'🔹 **Export** `{pre}export <poll_label>` or `/export <poll_label>`',
                            value='You can use this command or react with 📎 to a closed poll to generate a report. '
                                  'The report will then be sent to you in discord via the bot. This utf8-textfile '
                                  '(make sure to open it in an utf8-ready editor) will contain all the infos about the '
                                  'poll, including a detailed list of participants and their votes (just a list of names '
                                  'for anonymous polls).',
                            inline=False)
            embed.add_field(name=f'🔹 **Activate** `{pre}activate <poll_label>` or `/activate <poll_label>`',
                            value=f'To see how you can prepare inactive polls read the `{pre}prepare` command under Making '
                                  'New Polls. This command is used to manually activate a prepared poll.',
                            inline=False)

        elif page == '🛠':
            embed.add_field(name='🛠 Configuration',
                            value='To run any of these commands you need the **\"Manage Server\"** permisson.',
                            inline=False)
            embed.add_field(name=f'🔹 **Poll Admins** `{pre}adminrole <role name> (optional)` or `/adminrole <role name> (optional)`',
                            value='This gives the rights to create polls and to control ALL polls on the server. '
                                  f'To see the current role for poll admin, run the command without an argument: `{pre}adminrole`\n'
                                  'If you want to change the admin role to any other role, use the name of the new role '
                                  f'as the argument: `{pre}adminrole moderators`',
                            inline=False)
            embed.add_field(name=f'🔹 **Poll Users** `{pre}userrole <role name> (optional)` or `/userrole <role name> (optional)`',
                            value='Everything here is identical to the admin role, except that Poll Users can only '
                                  'control the polls which were created by themselves.',
                            inline=False)
            embed.add_field(name=f'🔹 **Change Prefix** `{pre}prefix <new_prefix>` or `/prefix <new_prefix>`',
                            value='This will change the bot prefix for your server. If you want to use a trailing '
                                  'whitespace, use "\w" instead of " " (discord deletes trailing whitespaces).',
                            inline=False)

        elif page == '❔':
            embed.add_field(name='❔ Debugging',
                            value='These commands are independent of your server prefix and serve to debug the bot.',
                            inline=False)
            embed.add_field(name=f'🔹 **Debug:** `@debug` or `/debug`',
                            value='This command will check the required permissions in the channel it is used and'
                                  'generate a short report with suggestions on your next actions.'
                                  'If you are stuck, please visit the support discord server.',
                            inline=False)
            embed.add_field(name=f'🔹 **Mention:** `@mention` | `@mention prefix` or `/mention <tag>`',
                            value='This is a prefix independent command to retrieve your prefix in case you changed '
                                  'and forgot it. More `@mention` tags might be added in the future.',
                            inline=False)

        elif page == '💖':
            embed.add_field(name='💖 RT Pollmaster 💖',
                            value='If you enjoy the bot, you can show your appreciation by giving him an upvote on Discordbots.',
                            inline=False)
            embed.add_field(name='🔹 **Developer**',
                            value='Original code by Newti#0654'
                                  '\nmodifed/fix/improved by RJGamer1002#8253',
                            inline=False)
            embed.add_field(name='🔹 **Support**',
                            value='You can support RT Pollmaster by sending an upvote his way or by clicking the donate link '
                                  'on the discordbots page:\n not available',
                            inline=False)
            embed.add_field(name='🔹 **Support Server**',
                            value='If you need help with RT Pollmaster, want to try him out or would like to give feedback '
                                  'to the developer, feel free to join the support server: https://discord.gg/sjrDM6WES2',
                            inline=False)
            embed.add_field(name='🔹 **Github**',
                            value='The full python source code is on my Github: https://github.com/RJ1002/pollmaster',
                            inline=False)
            embed.add_field(name='**Thanks for using RT Pollmaster!** 💗', value='Newti, RJGame1002', inline=False)
        else:
            return None

        return embed

    # @commands.hybrid_command(name="pmhelp",description="Display commands")

    @commands.hybrid_command(name="help", description="Display commands")
    async def pmhelp(self, ctx):
        server = await ask_for_server(self.bot, ctx.message)
        if not server:
            return

        permissions = ctx.message.channel.permissions_for(server.me)
        if not permissions.embed_links or not permissions.manage_messages or not permissions.add_reactions or not permissions.read_message_history:
            await ctx.reply("Error: Missing permissions. Type \"/debug.\"", delete_after=60)
            return

        if not isinstance(ctx.channel, discord.TextChannel):
            await ctx.response.send_message("`help` can only be used in a server text channel.", delete_after=60)
            return
        
        guild = ctx.guild
        if not guild:
            await ctx.response.send_message("Could not determine your server. Run the command in a server text channel.", delete_after=60)
            return

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

            if message.content.startswith(f"<@{self.bot.user.id}> mention"):
                channel = message.channel
                if not isinstance(channel, discord.TextChannel):
                    await channel.send("@mention can only be used in a server text channel.")
                    return

                guild = message.guild
                if not guild:
                    await channel.send("Could not determine your server.")
                    return

                if message.content == f"<@{self.bot.user.id}> mention":
                    await channel.send("The following mention tags are available:\n🔹 mention prefix")
                    return

                try:
                    tags = message.content.split()
                    tag = tags[len(tags)-1].lower()
                except IndexError:
                    await channel.send(f"Wrong formatting. Type \"@{self.bot.user.name} mention\" or "
                                       f"\"@{self.bot.user.name} mention <tag>\".")
                    return

                if tag == "prefix":
                    pre = await get_server_pre(self.bot, guild)
                    # await channel.send(f'The prefix for this server/channel is: \n {pre} \n To change it type: \n'
                    #                    f'{pre}prefix <new_prefix>')
                    await channel.send(pre)
                else:
                    await channel.send(f'Tag "{tag}" not found. Type `@{self.bot.user.name} mention` for a list of tags.')
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
        if not isinstance(ctx.channel, discord.TextChannel):
            await ctx.response.send_message("`debug` can only be used in a server text channel.", delete_after=60)
            return

        guild = ctx.guild
        if not guild:
            await ctx.response.send_message("Could not determine your server. Run the command in a server text channel.", delete_after=60)
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
        await ctx.response.send_message(status_msg, delete_after=60)
    tag = str
    @app_commands.command(name="mention", description="run mention")
    @app_commands.describe(
        tag='options: prefix',
    )
    async def pmmention(self, ctx, *, tag: tag = None):
        if not isinstance(ctx.channel, discord.TextChannel):
            await ctx.response.send_message("`/mention` can only be used in a server text channel.", delete_after=60)
            return

        guild = ctx.guild
        if not guild:
            await ctx.response.send_message("Could not determine your server.", delete_after=60)
            return
        if tag == "prefix":
            pre = await get_server_pre(self.bot, guild)
            await ctx.response.send_message(f'The prefix for this server/channel is: \n {pre} \n To change it type: \n'
                                f'{pre}prefix <new_prefix>', delete_after=60)
            #await ctx.response.send_message(pre)
        elif tag == None:
            await ctx.response.send_message("The following mention tags are available:\n🔹 prefix", delete_after=60)
        else:
            await ctx.response.send_message(f'Tag "{tag}" not found. Type `/mention` for a list of tags.', delete_after=60)
    @app_commands.command(name="ping", description="send a ping to bot")
    async def pmping(self, ctx):
        if not isinstance(ctx.channel, discord.TextChannel):
            await ctx.response.send_message("`/ping` can only be used in a server text channel.", delete_after=60)
            return
        guild = ctx.guild
        if not guild:
            await ctx.response.send_message("Could not determine your server. Run the command in a server text channel.", delete_after=60)
            return
        else:
            await ctx.response.send_message(f'Pong! In {round(ctx.client.latency * 1000)}ms', delete_after=60)
    

async def setup(bot):
    global logger
    logger = logging.getLogger('discord')
    await bot.add_cog(Help(bot))
