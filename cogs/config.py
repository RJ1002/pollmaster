import logging
import discord
from discord.ext import commands
from discord import app_commands
from discord import Role, User
from bson import ObjectId

class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    async def cog_command_error(self, ctx, error):
        if ctx.command.name == "adminrole":
            print('cog error adminrole!')
            await ctx.send(f'You don''t have permission to run this command! you need manage guild permission.', delete_after=60)
        if ctx.command.name == "userrole":
            print('cog error userrole!')
            await ctx.send(f'You don''t have permission to run this command! you need manage guild permission.', delete_after=60)
        if ctx.command.name == "prefix":
            print('cog error userrole!')
            await ctx.send(f'You don''t have permission to run this command! you need manage guild permission.', delete_after=60)
            
    async def cog_app_command_error(self, interaction, error):
        await interaction.response.defer(thinking=True)
        if interaction.command.name == "settings":
            await interaction.followup.send(f'You don''t have permission to run this command! you need manage guild permission.')
        if interaction.command.name == "adminrole":
            print('cog error adminrole!')
            await interaction.followup.send(f'You don''t have permission to run this command! you need manage guild permission.')
        if interaction.command.name == "userrole":
            print('cog error userrole!')
            await interaction.followup.send(f'You don''t have permission to run this command! you need manage guild permission.')

    @commands.hybrid_command(name="prefix", description="""Set a custom prefix for the server.""")
    @commands.has_permissions(manage_guild=True)
    @app_commands.describe(
        pre='Choose the new prefix you want',
    )
    async def prefix(self, ctx, *, pre:str=None):
        """Set a custom prefix for the server."""
        #server = ctx.message.guild
        #if pre.endswith('\w'):
        #    pre = pre[:-2]+' '
        #    if len(pre.strip()) > 0:
        #        msg = f'The server prefix has been set to `{pre}` Use `{pre}prefix <prefix>` to change it again.'
        #    else:
        #        await ctx.send('Invalid prefix.')
        #        return
        #else:
        #    msg = f'The server prefix has been set to `{pre}` Use `{pre}prefix <prefix>` to change it again. ' \
        #          f'If you would like to add a trailing whitespace to the prefix, use `{pre}prefix {pre}\w`.'

        #await self.bot.db.config.update_one({'_id': str(server.id)}, {'$set': {'prefix': str(pre)}}, upsert=True)
        #self.bot.pre[str(server.id)] = str(pre)
        msg = f'This command is **disabled** as of 4/24/2024 EST\nJoin the support server for more info or if you have any questions.'
        await ctx.send(msg)

    @app_commands.command(name="adminrole", description="Set or show the Admin Role. Members with this role can create polls and manage ALL polls.")
    #@commands.has_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(
        role='Choose the role for admin',
    )
    async def adminrole(self, ctx, *, role: Role = None):
        server = ctx.guild
        await ctx.response.defer(thinking=True)
        
        if not role:
            result = await self.bot.db.config.find_one({'_id': str(server.id)})
            if result and result.get('admin_role'):
                await ctx.followup.send(f'The admin role restricts which users are able to create and manage ALL polls on this server. \n'
                                   f'The current admin role is `{result.get("admin_role")}`. '
                                   f'To change it type `{result.get("prefix")}adminrole <role name>`')
            else:
                await ctx.followup.send(f'The admin role restricts which users are able to create and manage ALL polls on this server.  \n'
                                   f'No admin role set. '
                                   f'To set one type `{result.get("prefix")}adminrole <role name>`')
        elif role.name in [r.name for r in server.roles]:
            await self.bot.db.config.update_one({'_id': str(server.id)}, {'$set': {'admin_role': str(role)}}, upsert=True)
            await ctx.followup.send(f'Server role `{role}` can now manage all polls.')
        else:
            await ctx.followup.send(f'Server role `{role}` not found.')
        
    @app_commands.command(name="userrole", description="Set or show the User Role. Members with this role can create polls and manage their own polls.")
    #@commands.has_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(
        role='Choose the role for user',
    )
    async def userrole(self, ctx, *, role: Role=None):
        server = ctx.guild
        await ctx.response.defer(thinking=True)

        if not role:
            result = await self.bot.db.config.find_one({'_id': str(server.id)})
            if result and result.get('user_role'):
                await ctx.followup.send(f'The user role restricts which users are able to create and manage their own polls.  \n'
                                   f'The current user role is `{result.get("user_role")}`. '
                                   f'To change it type `{result.get("prefix")}userrole <role name>`')
            else:
                await ctx.followup.send(f'The user role restricts which users are able to create and manage their own polls.  \n'
                                   f'No user role set. '
                                   f'To set one type `{result.get("prefix")}userrole <role name>`')
        elif role.name in [r.name for r in server.roles]:
            await self.bot.db.config.update_one({'_id': str(server.id)}, {'$set': {'user_role': str(role)}}, upsert=True)
            await ctx.followup.send(f'Server role `{role}` can now create and manage their own polls.')
        else:
            await ctx.followup.send(f'Server role `{role}` not found.')
            
    @app_commands.command(name="settings", description="to change settings (Beta)")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(
        change=f'what setting do you want to change the status of',
    )
    @app_commands.choices(
        change=[discord.app_commands.Choice(name='pollclosed message', value=1), discord.app_commands.Choice(name='errormessage', value=2)],
    )
    async def settings(self, ctx, *, change: discord.app_commands.Choice[int]):
        server = ctx.guild
        result = await self.bot.db.config.find_one({'_id': str(server.id)},{'_id': 1, 'error_mess': 2, 'closedpoll_mess': 3 })
        await ctx.response.defer(thinking=True)
        print('settings message ran!')
        if change.name == "pollclosed message": #pollclosed message
            if result and not result.get('closedpoll_mess'):
                print('closed poll config not found!', result.get('closedpoll_mess'))
                await self.bot.db.config.update_one({'_id': str(server.id)}, {'$set': {'closedpoll_mess': 'True'}}, upsert=True)
                await ctx.followup.send("closed poll message was set to `enable`!!")
                
            elif result and result.get('closedpoll_mess'):
                print('closed poll resultget!', result.get('closedpoll_mess'))
                if result.get('closedpoll_mess') == 'True':
                    await self.bot.db.config.update_one({'_id': str(server.id)}, {'$set': {'closedpoll_mess': 'False'}}, upsert=True)
                    await ctx.followup.send("closed poll message was set to `disabled`!!")
                    print('closed poll result true')
                    
                elif result and result.get('closedpoll_mess') == 'False':
                    await self.bot.db.config.update_one({'_id': str(server.id)}, {'$set': {'closedpoll_mess': 'True'}}, upsert=True)
                    await ctx.followup.send("closed poll message was set to `enable`!!")
                    print('closed poll result false')
                else:
                    await ctx.followup.send("unknown error has occurred. please report to dev!")
            else:
                await ctx.followup.send("unknown error has occurred. please report to dev!")
        elif change.name == "errormessage": #errormessage
            if result and not result.get('error_mess'):
                print('error config not found!', result.get('error_mess'))
                await self.bot.db.config.update_one({'_id': str(server.id)}, {'$set': {'error_mess': 'True'}}, upsert=True)
                await ctx.followup.send("error messages was set to `enable`!!")
                
            elif result and result.get('error_mess'):
                print('error resultget!', result.get('error_mess'))
                if result.get('error_mess') == 'True':
                    await self.bot.db.config.update_one({'_id': str(server.id)}, {'$set': {'error_mess': 'False'}}, upsert=True)
                    await ctx.followup.send("error messages was set to `disabled`!!")
                    print('error result true')
                    
                elif result and result.get('error_mess') == 'False':
                    await self.bot.db.config.update_one({'_id': str(server.id)}, {'$set': {'error_mess': 'True'}}, upsert=True)
                    await ctx.followup.send("error messages was set to `enable`!!")
                    print('error result false')
                else:
                    await ctx.followup.send("unknown error has occurred. please report to dev!")
            else:
                await ctx.followup.send("unknown error has occurred. please report to dev!")
        else:
            await ctx.followup.send("unknown error has occured. please report to Dev!")


async def setup(bot):
    global logger
    logger = logging.getLogger('discord')
    await bot.add_cog(Config(bot))