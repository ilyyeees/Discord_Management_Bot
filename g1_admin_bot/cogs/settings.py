import discord
from discord.ext import commands
import json
import logging
import aiohttp
import os

logger = logging.getLogger("g1_admin.settings")

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = 'config.json'
        # Store config in bot for easy access from other cogs
        self.bot._config = self.load_config()
        
    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
            
    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.bot._config, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    async def cog_check(self, ctx):
        """Check if user has admin permissions for all commands in this cog"""
        if ctx.guild is None:
            return False
            
        # Commands in this cog are owner-only or administrator
        is_owner = await self.bot.is_owner(ctx.author)
        is_admin = ctx.author.guild_permissions.administrator
        
        if not (is_owner or is_admin):
            await ctx.send("Only the bot owner or server administrators can use this command.")
            
        return is_owner or is_admin
    
    @commands.command(name="setprefix")
    async def set_prefix(self, ctx, new_prefix=None):
        """
        Change the command prefix for the bot
        
        Usage: !setprefix <new_prefix>
        Example: !setprefix ?
        """
        if not new_prefix:
            current_prefix = self.bot._config.get("prefix", "!")
            await ctx.send(f"Current prefix is: `{current_prefix}`\nUse `{current_prefix}setprefix <new_prefix>` to change it.")
            return
            
        if len(new_prefix) > 5:
            await ctx.send("Prefix must be 5 characters or less.")
            return
            
        # Update prefix in config
        self.bot._config["prefix"] = new_prefix
        if self.save_config():
            # Update bot's command prefix
            self.bot.command_prefix = new_prefix
            await ctx.send(f"Prefix changed to: `{new_prefix}`")
            
            # Update bot's status
            await self.bot.change_presence(activity=discord.Game(name=f"Type {new_prefix}help"))
        else:
            await ctx.send("Failed to save the new prefix. See logs for details.")
    
    @commands.command(name="setpfp")
    async def set_profile_picture(self, ctx, url=None):
        """
        Change the bot's profile picture
        
        Usage: !setpfp <image_url>
        or attach an image with !setpfp
        """
        # Check for administrator or owner permissions (already in cog_check)
        
        # Get image from attachment or URL
        image_url = url
        if not image_url and ctx.message.attachments:
            image_url = ctx.message.attachments[0].url
            
        if not image_url:
            await ctx.send("Please provide an image URL or attach an image.")
            return
            
        try:
            # Download the image
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status != 200:
                        await ctx.send(f"Failed to download image. Status code: {resp.status}")
                        return
                        
                    image_data = await resp.read()
                    
            # Update the bot's profile picture
            await self.bot.user.edit(avatar=image_data)
            await ctx.send("Profile picture updated successfully!")
            
            # Log the change
            log_channel_id = self.bot._config.get("log_channel_id")
            if log_channel_id:
                log_channel = self.bot.get_channel(int(log_channel_id))
                if log_channel:
                    embed = discord.Embed(
                        title="Bot Profile Picture Updated",
                        description=f"Profile picture updated by {ctx.author.mention}",
                        color=discord.Color.green()
                    )
                    embed.set_thumbnail(url=self.bot.user.display_avatar.url)
                    await log_channel.send(embed=embed)
                    
        except discord.HTTPException as e:
            if e.code == 50035:
                await ctx.send("Image file size too large. Please use a smaller image.")
            else:
                await ctx.send(f"Failed to update profile picture: {e}")
            logger.error(f"Profile picture update failed: {e}")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")
            logger.error(f"Profile picture update failed: {e}")
    
    @commands.command(name="setlogchannel")
    async def set_log_channel(self, ctx, channel: discord.TextChannel = None):
        """
        Set the channel for bot logging
        
        Usage: !setlogchannel #channel-name
        Example: !setlogchannel #bot-logs
        """
        if channel is None:
            # If no channel provided, check if one is already set
            current_channel_id = self.bot._config.get("log_channel_id")
            if current_channel_id:
                current_channel = self.bot.get_channel(int(current_channel_id))
                if current_channel:
                    await ctx.send(f"Current log channel is: {current_channel.mention}")
                else:
                    await ctx.send(f"Current log channel ID is set but channel not found: {current_channel_id}")
            else:
                await ctx.send("No log channel currently set. Use this command with a channel mention to set one.")
            return
            
        # Update log channel in config
        self.bot._config["log_channel_id"] = str(channel.id)
        self.bot.log_channel_id = str(channel.id)  # Also store in bot for easy access
        
        if self.save_config():
            await ctx.send(f"Log channel set to: {channel.mention}")
            await channel.send(":information_source: This channel has been set as the bot's logging channel.")
        else:
            await ctx.send("Failed to save the log channel. See logs for details.")
    
    @commands.command(name="setadminrole")
    async def set_admin_role(self, ctx, role: discord.Role = None):
        """
        Add a role with admin permissions for bot commands
        
        Usage: !setadminrole @role
        Example: !setadminrole @Moderators
        """
        if role is None:
            # List current admin roles
            admin_role_ids = self.bot._config.get("admin_role_ids", [])
            if admin_role_ids:
                roles_mention = []
                for role_id in admin_role_ids:
                    role = ctx.guild.get_role(int(role_id))
                    if role:
                        roles_mention.append(role.mention)
                if roles_mention:
                    await ctx.send(f"Current admin roles: {', '.join(roles_mention)}")
                else:
                    await ctx.send("Admin roles are set but not found in the server.")
            else:
                await ctx.send("No admin roles currently set.")
            return
            
        # Add role to admin roles if not already there
        admin_role_ids = self.bot._config.get("admin_role_ids", [])
        if str(role.id) not in admin_role_ids:
            admin_role_ids.append(str(role.id))
            self.bot._config["admin_role_ids"] = admin_role_ids
            
            if self.save_config():
                await ctx.send(f"Added {role.mention} to admin roles.")
            else:
                await ctx.send("Failed to save admin role. See logs for details.")
        else:
            await ctx.send(f"{role.mention} is already an admin role.")
    
    @commands.command(name="removeadminrole")
    async def remove_admin_role(self, ctx, role: discord.Role):
        """
        Remove a role from having admin permissions for bot commands
        
        Usage: !removeadminrole @role
        Example: !removeadminrole @Moderators
        """
        admin_role_ids = self.bot._config.get("admin_role_ids", [])
        if str(role.id) in admin_role_ids:
            admin_role_ids.remove(str(role.id))
            self.bot._config["admin_role_ids"] = admin_role_ids
            
            if self.save_config():
                await ctx.send(f"Removed {role.mention} from admin roles.")
            else:
                await ctx.send("Failed to remove admin role. See logs for details.")
        else:
            await ctx.send(f"{role.mention} is not an admin role.")
    
    @commands.command(name="config")
    async def show_config(self, ctx):
        """
        Show the current bot configuration
        
        Usage: !config
        """
        # Create a safe version of config to display (without token)
        safe_config = {k: v for k, v in self.bot._config.items() if k != "token"}
        
        # Format admin roles as mentions
        if "admin_role_ids" in safe_config and safe_config["admin_role_ids"]:
            admin_roles = []
            for role_id in safe_config["admin_role_ids"]:
                role = ctx.guild.get_role(int(role_id))
                if role:
                    admin_roles.append(role.name)
                else:
                    admin_roles.append(f"Unknown Role ({role_id})")
            safe_config["admin_roles"] = admin_roles
            
        # Format log channel as name
        if "log_channel_id" in safe_config and safe_config["log_channel_id"]:
            log_channel = self.bot.get_channel(int(safe_config["log_channel_id"]))
            if log_channel:
                safe_config["log_channel"] = log_channel.name
            else:
                safe_config["log_channel"] = f"Unknown Channel ({safe_config['log_channel_id']})"
            
        # Create and send embed
        embed = discord.Embed(
            title="Bot Configuration",
            color=discord.Color.blue()
        )
        
        # Add fields for each config item
        for key, value in safe_config.items():
            if key not in ["admin_role_ids", "log_channel_id", "token"]:  # Skip raw IDs
                if isinstance(value, list):
                    value = ", ".join(value) if value else "None"
                embed.add_field(name=key.replace("_", " ").title(), value=value, inline=False)
                
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Settings(bot)) 