import logging
import discord
from discord.ext import commands
from discord import app_commands
from discord import Role, User
from bson import ObjectId

class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="prefix", description="""Set a custom prefix for the server.""")
    @commands.has_permissions(manage_guild=True)
    @app_commands.describe(
        pre='Choose the new prefix you want',
    )
    async def prefix(self, ctx, *, pre:str):
        """Set a custom prefix for the server."""
        server = ctx.message.guild
        if pre.endswith('\w'):
            pre = pre[:-2]+' '
            if len(pre.strip()) > 0:
                msg = f'The server prefix has been set to `{pre}` Use `{pre}prefix <prefix>` to change it again.'
            else:
                await ctx.send('Invalid prefix.')
                return
        else:
            msg = f'The server prefix has been set to `{pre}` Use `{pre}prefix <prefix>` to change it again. ' \
                  f'If you would like to add a trailing whitespace to the prefix, use `{pre}prefix {pre}\w`.'

        await self.bot.db.config.update_one({'_id': str(server.id)}, {'$set': {'prefix': str(pre)}}, upsert=True)
        self.bot.pre[str(server.id)] = str(pre)
        await ctx.send(msg)

    @commands.hybrid_command(name="adminrole", description="Set or show the Admin Role. Members with this role can create polls and manage ALL polls.")
    @commands.has_permissions(manage_guild=True)
    @app_commands.describe(
        role='Choose the role for admin',
    )
    async def adminrole(self, ctx, *, role: Role = None):
        server = ctx.message.guild
        
        if not role:
            result = await self.bot.db.config.find_one({'_id': str(server.id)})
            if result and result.get('admin_role'):
                await ctx.send(f'The admin role restricts which users are able to create and manage ALL polls on this server. \n'
                                   f'The current admin role is `{result.get("admin_role")}`. '
                                   f'To change it type `{result.get("prefix")}adminrole <role name>`')
            else:
                await ctx.send(f'The admin role restricts which users are able to create and manage ALL polls on this server.  \n'
                                   f'No admin role set. '
                                   f'To set one type `{result.get("prefix")}adminrole <role name>`')
        elif role.name in [r.name for r in server.roles]:
            await self.bot.db.config.update_one({'_id': str(server.id)}, {'$set': {'admin_role': str(role)}}, upsert=True)
            await ctx.send(f'Server role `{role}` can now manage all polls.')
        else:
            await ctx.send(f'Server role `{role}` not found.')
        
    @commands.hybrid_command(name="userrole", description="Set or show the User Role. Members with this role can create polls and manage their own polls.")
    @commands.has_permissions(manage_guild=True)
    @app_commands.describe(
        role='Choose the role for user',
    )
    async def userrole(self, ctx, *, role: Role=None):
        server = ctx.message.guild

        if not role:
            result = await self.bot.db.config.find_one({'_id': str(server.id)})
            if result and result.get('user_role'):
                await ctx.send(f'The user role restricts which users are able to create and manage their own polls.  \n'
                                   f'The current user role is `{result.get("user_role")}`. '
                                   f'To change it type `{result.get("prefix")}userrole <role name>`')
            else:
                await ctx.send(f'The user role restricts which users are able to create and manage their own polls.  \n'
                                   f'No user role set. '
                                   f'To set one type `{result.get("prefix")}userrole <role name>`')
        elif role.name in [r.name for r in server.roles]:
            await self.bot.db.config.update_one({'_id': str(server.id)}, {'$set': {'user_role': str(role)}}, upsert=True)
            await ctx.send(f'Server role `{role}` can now create and manage their own polls.')
        else:
            await ctx.send(f'Server role `{role}` not found.')
            
    @app_commands.command(name="errormessage", description="to enable or disable error message (Beta)")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def errormessage(self, ctx):
        print('error message ran!')
        server = ctx.guild
        result = await self.bot.db.config.find_one({'_id': str(server.id)},{'_id': 1, 'error_mess': 2})
        
        if result and not result.get('error_mess'):
            print('error config not found!', result.get('error_mess'))
            await self.bot.db.config.update_one({'_id': str(server.id)}, {'$set': {'error_mess': 'True'}}, upsert=True)
            await ctx.response.send_message("error messages was set to `enable`!!", delete_after=60)
            
        elif result and result.get('error_mess'):
            print('error resultget!', result.get('error_mess'))
            if result.get('error_mess') == 'True':
                await self.bot.db.config.update_one({'_id': str(server.id)}, {'$set': {'error_mess': 'False'}}, upsert=True)
                await ctx.response.send_message("error messages was set to `disabled`!!", delete_after=60)
                print('error result true')
                
            elif result and result.get('error_mess') == 'False':
                await self.bot.db.config.update_one({'_id': str(server.id)}, {'$set': {'error_mess': 'True'}}, upsert=True)
                await ctx.response.send_message("error messages was set to `enable`!!", delete_after=60)
                print('error result false')
            else:
                await ctx.response.send_message("unknown error has occurred. please report to dev!", delete_after=60)
        else:
            await ctx.response.send_message("unknown error has occurred. please report to dev!", delete_after=60)


async def setup(bot):
    global logger
    logger = logging.getLogger('discord')
    await bot.add_cog(Config(bot))