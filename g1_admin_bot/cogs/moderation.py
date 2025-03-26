import discord
from discord.ext import commands
import logging
import asyncio
import datetime

logger = logging.getLogger("g1_admin.moderation")

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    async def log_moderation_action(self, action, member, moderator, reason=None, duration=None):
        """Log moderation actions to the configured log channel"""
        # Skip if no log channel configured
        log_channel_id = getattr(self.bot, "log_channel_id", None) or getattr(self.bot, "_config", {}).get("log_channel_id")
        if not log_channel_id:
            return
            
        log_channel = self.bot.get_channel(int(log_channel_id))
        if not log_channel:
            return
            
        # Create embed for logging
        embed = discord.Embed(
            title=f"Moderation Action: {action}",
            color=discord.Color.red(),
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
        embed.add_field(name="Moderator", value=f"{moderator} ({moderator.id})", inline=False)
        
        if reason:
            embed.add_field(name="Reason", value=reason, inline=False)
            
        if duration:
            embed.add_field(name="Duration", value=duration, inline=False)
            
        # Add user avatar
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await log_channel.send(embed=embed)
    
    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick_member(self, ctx, member: discord.Member, *, reason=None):
        """
        Kick a member from the server
        
        Usage: !kick @user [reason]
        Example: !kick @User123 Breaking server rules
        """
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            await ctx.send("You cannot kick someone with a higher or equal role.")
            return
            
        reason = reason or "No reason provided"
        
        try:
            # Try to send a DM to the user
            try:
                embed = discord.Embed(
                    title=f"You have been kicked from {ctx.guild.name}",
                    description=f"Reason: {reason}",
                    color=discord.Color.red()
                )
                await member.send(embed=embed)
            except:
                # Can't send DM, continue with kick
                pass
                
            await member.kick(reason=reason)
            await ctx.send(f"✅ {member.mention} has been kicked. Reason: {reason}")
            
            # Log the action
            await self.log_moderation_action("Kick", member, ctx.author, reason)
            
        except discord.Forbidden:
            await ctx.send("I don't have permission to kick that member.")
        except Exception as e:
            logger.error(f"Error kicking member: {e}")
            await ctx.send(f"An error occurred: {e}")
            
    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban_member(self, ctx, member: discord.Member, *, reason=None):
        """
        Ban a member from the server
        
        Usage: !ban @user [reason]
        Example: !ban @User123 Repeated rule violations
        """
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            await ctx.send("You cannot ban someone with a higher or equal role.")
            return
            
        reason = reason or "No reason provided"
        
        try:
            # Try to send a DM to the user
            try:
                embed = discord.Embed(
                    title=f"You have been banned from {ctx.guild.name}",
                    description=f"Reason: {reason}",
                    color=discord.Color.red()
                )
                await member.send(embed=embed)
            except:
                # Can't send DM, continue with ban
                pass
                
            await member.ban(reason=reason, delete_message_days=1)
            await ctx.send(f"✅ {member.mention} has been banned. Reason: {reason}")
            
            # Log the action
            await self.log_moderation_action("Ban", member, ctx.author, reason)
            
        except discord.Forbidden:
            await ctx.send("I don't have permission to ban that member.")
        except Exception as e:
            logger.error(f"Error banning member: {e}")
            await ctx.send(f"An error occurred: {e}")
    
    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban_member(self, ctx, user_id: int, *, reason=None):
        """
        Unban a user by ID
        
        Usage: !unban <user_id> [reason]
        Example: !unban 123456789012345678 Appealed ban
        """
        reason = reason or "No reason provided"
        
        try:
            # Get the banned user
            ban_entries = [ban async for ban in ctx.guild.bans()]
            banned_user = discord.utils.get(ban_entries, user__id=user_id)
            
            if not banned_user:
                await ctx.send(f"No banned user found with ID {user_id}")
                return
                
            await ctx.guild.unban(banned_user.user, reason=reason)
            await ctx.send(f"✅ {banned_user.user} has been unbanned. Reason: {reason}")
            
            # Log the action
            await self.log_moderation_action("Unban", banned_user.user, ctx.author, reason)
            
        except discord.Forbidden:
            await ctx.send("I don't have permission to unban users.")
        except Exception as e:
            logger.error(f"Error unbanning user: {e}")
            await ctx.send(f"An error occurred: {e}")
            
    @commands.command(name="mute")
    @commands.has_permissions(manage_roles=True)
    async def mute_member(self, ctx, member: discord.Member, duration: str = None, *, reason=None):
        """
        Mute a member (timeout)
        
        Usage: !mute @user [duration] [reason]
        Example: !mute @User123 1h Spamming
        
        Duration format: 
        - xm = x minutes
        - xh = x hours
        - xd = x days
        - If no duration is provided, default is 1 hour
        """
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            await ctx.send("You cannot mute someone with a higher or equal role.")
            return
            
        reason = reason or "No reason provided"
        
        # Parse duration
        duration_seconds = 3600  # Default: 1 hour
        duration_text = "1 hour"
        
        if duration:
            try:
                if duration.endswith('m'):
                    duration_seconds = int(duration[:-1]) * 60
                    duration_text = f"{duration[:-1]} minute(s)"
                elif duration.endswith('h'):
                    duration_seconds = int(duration[:-1]) * 3600
                    duration_text = f"{duration[:-1]} hour(s)"
                elif duration.endswith('d'):
                    duration_seconds = int(duration[:-1]) * 86400
                    duration_text = f"{duration[:-1]} day(s)"
                else:
                    # Assume minutes if no unit specified
                    duration_seconds = int(duration) * 60
                    duration_text = f"{duration} minute(s)"
            except ValueError:
                await ctx.send("Invalid duration format. Use a number followed by m, h, or d (e.g., 30m, 1h, 1d)")
                return
                
        # Limit to max Discord timeout (28 days)
        if duration_seconds > 2419200:  # 28 days in seconds
            duration_seconds = 2419200
            duration_text = "28 days (maximum)"
            
        try:
            # Apply timeout
            until = discord.utils.utcnow() + datetime.timedelta(seconds=duration_seconds)
            await member.timeout(until, reason=reason)
            
            await ctx.send(f"✅ {member.mention} has been muted for {duration_text}. Reason: {reason}")
            
            # Try to DM the user
            try:
                embed = discord.Embed(
                    title=f"You have been muted in {ctx.guild.name}",
                    description=f"Duration: {duration_text}\nReason: {reason}",
                    color=discord.Color.orange()
                )
                await member.send(embed=embed)
            except:
                pass
                
            # Log the action
            await self.log_moderation_action("Mute", member, ctx.author, reason, duration_text)
            
        except discord.Forbidden:
            await ctx.send("I don't have permission to mute that member.")
        except Exception as e:
            logger.error(f"Error muting member: {e}")
            await ctx.send(f"An error occurred: {e}")
    
    @commands.command(name="unmute")
    @commands.has_permissions(manage_roles=True)
    async def unmute_member(self, ctx, member: discord.Member, *, reason=None):
        """
        Unmute a member (remove timeout)
        
        Usage: !unmute @user [reason]
        Example: !unmute @User123 Good behavior
        """
        reason = reason or "No reason provided"
        
        try:
            # Remove timeout
            await member.timeout(None, reason=reason)
            await ctx.send(f"✅ {member.mention} has been unmuted. Reason: {reason}")
            
            # Log the action
            await self.log_moderation_action("Unmute", member, ctx.author, reason)
            
        except discord.Forbidden:
            await ctx.send("I don't have permission to unmute that member.")
        except Exception as e:
            logger.error(f"Error unmuting member: {e}")
            await ctx.send(f"An error occurred: {e}")
    
    @commands.command(name="purge", aliases=["clear"])
    @commands.has_permissions(manage_messages=True)
    async def purge_messages(self, ctx, amount: int, user: discord.Member = None):
        """
        Purge messages from a channel
        
        Usage: !purge <amount> [@user]
        Example: !purge 10 @User123
        """
        if amount <= 0 or amount > 100:
            await ctx.send("Please provide a number between 1 and 100.")
            return
            
        # Delete the command message first
        await ctx.message.delete()
        
        # Define check based on user
        def check(msg):
            return user is None or msg.author == user
            
        # Purge messages
        try:
            deleted = await ctx.channel.purge(limit=amount, check=check)
            confirm_msg = await ctx.send(f"✅ Deleted {len(deleted)} messages.")
            
            # Log the action
            log_channel_id = getattr(self.bot, "log_channel_id", None) or getattr(self.bot, "_config", {}).get("log_channel_id")
            if log_channel_id:
                log_channel = self.bot.get_channel(int(log_channel_id))
                if log_channel:
                    if user:
                        await log_channel.send(f"🗑️ **{ctx.author}** purged {len(deleted)} messages from {user} in {ctx.channel.mention}")
                    else:
                        await log_channel.send(f"🗑️ **{ctx.author}** purged {len(deleted)} messages in {ctx.channel.mention}")
                        
            # Auto-delete confirmation message after 5 seconds
            await asyncio.sleep(5)
            await confirm_msg.delete()
            
        except discord.Forbidden:
            await ctx.send("I don't have permission to delete messages.")
        except discord.HTTPException as e:
            await ctx.send(f"Error deleting messages: {e}")
            
    @commands.command(name="addrole")
    @commands.has_permissions(manage_roles=True)
    async def add_role(self, ctx, member: discord.Member, *, role: discord.Role):
        """
        Add a role to a member
        
        Usage: !addrole @user @role
        Example: !addrole @User123 @Member
        """
        if role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            await ctx.send("You cannot assign a role that is higher than or equal to your highest role.")
            return
            
        if role in member.roles:
            await ctx.send(f"{member.mention} already has the {role.mention} role.")
            return
            
        try:
            await member.add_roles(role, reason=f"Role added by {ctx.author}")
            await ctx.send(f"✅ Added {role.mention} to {member.mention}")
            
            # Log the action
            await self.log_moderation_action("Role Add", member, ctx.author, f"Added role: {role.name}")
            
        except discord.Forbidden:
            await ctx.send("I don't have permission to manage that role.")
        except Exception as e:
            logger.error(f"Error adding role: {e}")
            await ctx.send(f"An error occurred: {e}")
            
    @commands.command(name="removerole")
    @commands.has_permissions(manage_roles=True)
    async def remove_role(self, ctx, member: discord.Member, *, role: discord.Role):
        """
        Remove a role from a member
        
        Usage: !removerole @user @role
        Example: !removerole @User123 @Member
        """
        if role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            await ctx.send("You cannot remove a role that is higher than or equal to your highest role.")
            return
            
        if role not in member.roles:
            await ctx.send(f"{member.mention} doesn't have the {role.mention} role.")
            return
            
        try:
            await member.remove_roles(role, reason=f"Role removed by {ctx.author}")
            await ctx.send(f"✅ Removed {role.mention} from {member.mention}")
            
            # Log the action
            await self.log_moderation_action("Role Remove", member, ctx.author, f"Removed role: {role.name}")
            
        except discord.Forbidden:
            await ctx.send("I don't have permission to manage that role.")
        except Exception as e:
            logger.error(f"Error removing role: {e}")
            await ctx.send(f"An error occurred: {e}")
    
    @commands.command(name="warn")
    @commands.has_permissions(manage_messages=True)
    async def warn_member(self, ctx, member: discord.Member, *, reason=None):
        """
        Warn a member
        
        Usage: !warn @user [reason]
        Example: !warn @User123 Spamming in chat
        """
        if member.bot:
            await ctx.send("Cannot warn bots.")
            return
            
        reason = reason or "No reason provided"
        
        # Send warning to channel
        await ctx.send(f"⚠️ {member.mention} has been warned. Reason: {reason}")
        
        # Try to DM the user
        try:
            embed = discord.Embed(
                title=f"Warning from {ctx.guild.name}",
                description=f"You have been warned by {ctx.author}.\nReason: {reason}",
                color=discord.Color.gold()
            )
            if ctx.guild.icon:
                embed.set_thumbnail(url=ctx.guild.icon.url)
            await member.send(embed=embed)
        except:
            await ctx.send("Note: Unable to send DM to user.")
            
        # Log the warning
        await self.log_moderation_action("Warning", member, ctx.author, reason)

    @kick_member.error
    @ban_member.error
    @unban_member.error
    @mute_member.error
    @unmute_member.error
    @purge_messages.error
    @add_role.error
    @remove_role.error
    async def moderation_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have the required permissions to use this command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument. Please check `{ctx.prefix}help {ctx.command.name}`")
        elif isinstance(error, commands.BadArgument):
            if ctx.command.name == "unban":
                await ctx.send("Please provide a valid user ID to unban.")
            else:
                await ctx.send("Could not find that member. Please mention a valid member or provide a valid ID.")
        else:
            logger.error(f"Error in {ctx.command.name}: {error}")
            await ctx.send(f"An error occurred: {error}")

async def setup(bot):
    await bot.add_cog(Moderation(bot)) 