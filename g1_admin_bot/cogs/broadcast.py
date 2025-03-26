import discord
from discord.ext import commands
import logging
import asyncio

logger = logging.getLogger("g1_admin.broadcast")

class Broadcast(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    async def cog_check(self, ctx):
        """Check if user has admin permissions for all commands in this cog"""
        if ctx.guild is None:
            return False
        
        # Get admin role IDs from config
        config = self.bot._config if hasattr(self.bot, "_config") else {}
        admin_role_ids = config.get("admin_role_ids", [])
        
        # Check if user has admin role or is administrator
        is_admin = ctx.author.guild_permissions.administrator
        
        if not is_admin and admin_role_ids:
            for role in ctx.author.roles:
                if str(role.id) in admin_role_ids:
                    is_admin = True
                    break
                    
        if not is_admin:
            await ctx.send("You don't have permission to use this command.")
            
        return is_admin
    
    @commands.command(name="broadcast")
    async def broadcast_message(self, ctx, *, message=None):
        """
        Broadcast a message to all members of the server
        
        Usage: !broadcast <message>
        Example: !broadcast Server will be down for maintenance in 1 hour.
        
        You can use these variables in your message:
        {user} - Mentions the user
        {username} - The user's name
        {server} - The server name
        """
        if not message:
            await ctx.send("Please provide a message to broadcast.")
            return
            
        # Confirmation message
        confirm_msg = await ctx.send(f"Are you sure you want to send this message to all members?\n"
                                    f"```{message}```\n"
                                    f"Variables like {{user}} will be replaced with the member's mention.\n"
                                    f"React with ✅ to confirm or ❌ to cancel.")
        
        # Add reaction options
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirm_msg.id
            
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            
            if str(reaction.emoji) == "❌":
                await ctx.send("Broadcast cancelled.")
                return
                
            if str(reaction.emoji) == "✅":
                # Start broadcasting
                status_message = await ctx.send("Broadcasting message... 0% complete")
                
                members = ctx.guild.members
                success_count = 0
                fail_count = 0
                
                # Log to bot's log channel if configured
                log_channel_id = getattr(self.bot, "log_channel_id", None)
                log_channel = None
                if log_channel_id:
                    log_channel = self.bot.get_channel(int(log_channel_id))
                    if log_channel:
                        log_embed = discord.Embed(
                            title="📣 Broadcast Initiated",
                            description=f"Broadcast initiated by {ctx.author.mention}\nMessage: ```{message}```",
                            color=discord.Color.blue()
                        )
                        log_embed.set_footer(text=getattr(self.bot, "author", "G1 Admin"))
                        await log_channel.send(embed=log_embed)
                
                # Send DMs with progress updates
                for i, member in enumerate(members):
                    if member.bot:
                        continue
                        
                    try:
                        # Format message with member variables
                        formatted_message = message.replace("{user}", member.mention)
                        formatted_message = formatted_message.replace("{username}", member.display_name)
                        formatted_message = formatted_message.replace("{server}", ctx.guild.name)
                        
                        # Create embed for DM
                        embed = discord.Embed(
                            title=f"Announcement from {ctx.guild.name}",
                            description=formatted_message,
                            color=discord.Color.blue()
                        )
                        embed.set_footer(text=f"Sent by {ctx.author} | {getattr(self.bot, 'author', 'G1 Admin')}")
                        if ctx.guild.icon:
                            embed.set_thumbnail(url=ctx.guild.icon.url)
                        
                        await member.send(embed=embed)
                        success_count += 1
                    except Exception as e:
                        logger.error(f"Failed to send DM to {member}: {e}")
                        fail_count += 1
                        
                    # Update progress every 5 members or at the end
                    if (i + 1) % 5 == 0 or i == len(members) - 1:
                        progress = int((i + 1) / len(members) * 100)
                        await status_message.edit(content=f"Broadcasting message... {progress}% complete")
                        await asyncio.sleep(0.5)  # Rate limiting prevention
                
                # Final report
                result_embed = discord.Embed(
                    title="📣 Broadcast Complete",
                    description=f"Message sent to {success_count} members. Failed: {fail_count}.",
                    color=discord.Color.green()
                )
                result_embed.set_footer(text=getattr(self.bot, "author", "G1 Admin"))
                await ctx.send(embed=result_embed)
                
                if log_channel:
                    complete_embed = discord.Embed(
                        title="✅ Broadcast Complete",
                        description=f"Sent to {success_count} members. Failed: {fail_count}.",
                        color=discord.Color.green()
                    )
                    complete_embed.set_footer(text=getattr(self.bot, "author", "G1 Admin"))
                    await log_channel.send(embed=complete_embed)
        
        except asyncio.TimeoutError:
            await ctx.send("Broadcast cancelled - you didn't respond in time.")
    
    @commands.command(name="dmuser")
    async def dm_user(self, ctx, user: discord.Member, *, message=None):
        """
        Send a direct message to a specific user
        
        Usage: !dmuser @username <message>
        Example: !dmuser @User123 Please follow the server rules.
        
        You can use these variables in your message:
        {user} - Mentions the user
        {username} - The user's name
        {server} - The server name
        """
        if not message:
            await ctx.send("Please provide a message to send.")
            return
            
        try:
            # Format message with user variables
            formatted_message = message.replace("{user}", user.mention)
            formatted_message = formatted_message.replace("{username}", user.display_name)
            formatted_message = formatted_message.replace("{server}", ctx.guild.name)
            
            embed = discord.Embed(
                title=f"Message from {ctx.guild.name}",
                description=formatted_message,
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Sent by {ctx.author} | {getattr(self.bot, 'author', 'G1 Admin')}")
            if ctx.guild.icon:
                embed.set_thumbnail(url=ctx.guild.icon.url)
                
            await user.send(embed=embed)
            
            result_embed = discord.Embed(
                title="✅ Message Sent",
                description=f"Message sent to {user.mention}.",
                color=discord.Color.green()
            )
            result_embed.set_footer(text=getattr(self.bot, "author", "G1 Admin"))
            await ctx.send(embed=result_embed)
            
            # Log to bot's log channel if configured
            log_channel_id = getattr(self.bot, "log_channel_id", None)
            if log_channel_id:
                log_channel = self.bot.get_channel(int(log_channel_id))
                if log_channel:
                    log_embed = discord.Embed(
                        title="✉️ DM Sent",
                        description=f"DM sent by {ctx.author.mention} to {user.mention}\nMessage: ```{message}```",
                        color=discord.Color.blue()
                    )
                    log_embed.set_footer(text=getattr(self.bot, "author", "G1 Admin"))
                    await log_channel.send(embed=log_embed)
                    
        except Exception as e:
            logger.error(f"Failed to send DM to {user}: {e}")
            await ctx.send(f"Failed to send message to {user.mention}. They may have DMs disabled.")

async def setup(bot):
    await bot.add_cog(Broadcast(bot)) 