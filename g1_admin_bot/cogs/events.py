import discord
from discord.ext import commands
import logging
import json
import random

logger = logging.getLogger("g1_admin.events")

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Default welcome and goodbye messages
        self.default_welcome = [
            "Welcome {user} to {server}! Enjoy your stay!",
            "Hey {user}, welcome to {server}! We're glad to have you!",
            "{user} just joined {server}! Everyone say hello!"
        ]
        self.default_goodbye = [
            "{user} has left {server}. We'll miss you!",
            "Goodbye {user}! We hope to see you again soon!",
            "{user} has left the server. Farewell!"
        ]
        
        # Load custom messages if available
        self.load_messages()
        
    def load_messages(self):
        """Load custom welcome and goodbye messages from config"""
        try:
            config = getattr(self.bot, "_config", {})
            
            # If welcome messages exist in config, use them
            if "welcome_messages" in config and config["welcome_messages"]:
                self.welcome_messages = config["welcome_messages"]
            else:
                self.welcome_messages = self.default_welcome
                
            # If goodbye messages exist in config, use them
            if "goodbye_messages" in config and config["goodbye_messages"]:
                self.goodbye_messages = config["goodbye_messages"]
            else:
                self.goodbye_messages = self.default_goodbye
                
            # Get welcome and goodbye channels
            self.welcome_channel_id = config.get("welcome_channel_id")
            self.goodbye_channel_id = config.get("goodbye_channel_id")
            
        except Exception as e:
            logger.error(f"Error loading welcome/goodbye messages: {e}")
            self.welcome_messages = self.default_welcome
            self.goodbye_messages = self.default_goodbye
            self.welcome_channel_id = None
            self.goodbye_channel_id = None
            
    def save_messages(self):
        """Save custom welcome and goodbye messages to config"""
        try:
            config = getattr(self.bot, "_config", {})
            
            config["welcome_messages"] = self.welcome_messages
            config["goodbye_messages"] = self.goodbye_messages
            config["welcome_channel_id"] = self.welcome_channel_id
            config["goodbye_channel_id"] = self.goodbye_channel_id
            
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=4)
                
            return True
        except Exception as e:
            logger.error(f"Error saving welcome/goodbye messages: {e}")
            return False
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Send welcome message when a new member joins"""
        if member.bot:
            return  # Skip bots if desired
            
        # Get the welcome channel
        welcome_channel_id = self.welcome_channel_id
        if not welcome_channel_id:
            return
            
        welcome_channel = member.guild.get_channel(int(welcome_channel_id))
        if not welcome_channel:
            return
            
        # Select a random welcome message
        message = random.choice(self.welcome_messages)
        
        # Format the message with user and server info
        message = message.replace("{user}", member.mention)
        message = message.replace("{server}", member.guild.name)
        message = message.replace("{username}", str(member))
        message = message.replace("{count}", str(member.guild.member_count))
        
        # Create an embed
        embed = discord.Embed(
            title="Welcome to the server!",
            description=message,
            color=discord.Color.green()
        )
        
        # Add user avatar
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Add server icon if available
        if member.guild.icon:
            embed.set_footer(text=f"{member.guild.name} • Member #{member.guild.member_count}", icon_url=member.guild.icon.url)
        else:
            embed.set_footer(text=f"{member.guild.name} • Member #{member.guild.member_count}")
            
        try:
            await welcome_channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Error sending welcome message: {e}")
            
        # Log to bot's log channel if configured
        log_channel_id = getattr(self.bot, "log_channel_id", None) or getattr(self.bot, "_config", {}).get("log_channel_id")
        if log_channel_id:
            log_channel = self.bot.get_channel(int(log_channel_id))
            if log_channel:
                await log_channel.send(f"➡️ **New member joined**: {member.mention} ({member})")
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Send goodbye message when a member leaves"""
        if member.bot:
            return  # Skip bots if desired
            
        # Get the goodbye channel
        goodbye_channel_id = self.goodbye_channel_id
        if not goodbye_channel_id:
            return
            
        goodbye_channel = member.guild.get_channel(int(goodbye_channel_id))
        if not goodbye_channel:
            return
            
        # Select a random goodbye message
        message = random.choice(self.goodbye_messages)
        
        # Format the message with user and server info
        message = message.replace("{user}", str(member))
        message = message.replace("{server}", member.guild.name)
        message = message.replace("{username}", str(member))
        message = message.replace("{count}", str(member.guild.member_count))
        
        # Create an embed
        embed = discord.Embed(
            title="Member Left",
            description=message,
            color=discord.Color.red()
        )
        
        # Add user avatar
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Add server icon if available
        if member.guild.icon:
            embed.set_footer(text=f"{member.guild.name} • Now {member.guild.member_count} members", icon_url=member.guild.icon.url)
        else:
            embed.set_footer(text=f"{member.guild.name} • Now {member.guild.member_count} members")
            
        try:
            await goodbye_channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Error sending goodbye message: {e}")
            
        # Log to bot's log channel if configured
        log_channel_id = getattr(self.bot, "log_channel_id", None) or getattr(self.bot, "_config", {}).get("log_channel_id")
        if log_channel_id:
            log_channel = self.bot.get_channel(int(log_channel_id))
            if log_channel:
                await log_channel.send(f"⬅️ **Member left**: {member} ({member.id})")
    
    @commands.group(name="welcome", invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def welcome(self, ctx):
        """
        Welcome message commands
        
        Usage: !welcome [set, add, remove, channel, test]
        """
        await ctx.send("Welcome message commands:\n"
                     f"`{ctx.prefix}welcome channel #channel` - Set welcome channel\n"
                     f"`{ctx.prefix}welcome add <message>` - Add a welcome message\n"
                     f"`{ctx.prefix}welcome remove <number>` - Remove a welcome message\n"
                     f"`{ctx.prefix}welcome list` - List all welcome messages\n"
                     f"`{ctx.prefix}welcome test` - Test welcome message\n\n"
                     "Available placeholders: {user}, {server}, {username}, {count}")
    
    @welcome.command(name="channel")
    async def welcome_channel(self, ctx, channel: discord.TextChannel = None):
        """
        Set the welcome message channel
        
        Usage: !welcome channel #channel
        Example: !welcome channel #welcome
        """
        if channel is None:
            # Show current welcome channel
            if self.welcome_channel_id:
                current_channel = ctx.guild.get_channel(int(self.welcome_channel_id))
                if current_channel:
                    await ctx.send(f"Current welcome channel is: {current_channel.mention}")
                else:
                    await ctx.send(f"Current welcome channel is set but not found: {self.welcome_channel_id}")
            else:
                await ctx.send("No welcome channel is set. Use this command with a channel mention to set one.")
            return
            
        # Set the welcome channel
        self.welcome_channel_id = str(channel.id)
        if self.save_messages():
            await ctx.send(f"Welcome channel set to: {channel.mention}")
        else:
            await ctx.send("Failed to save welcome channel.")
    
    @welcome.command(name="add")
    async def welcome_add(self, ctx, *, message: str):
        """
        Add a welcome message
        
        Usage: !welcome add <message>
        Example: !welcome add Welcome {user} to {server}!
        """
        self.welcome_messages.append(message)
        if self.save_messages():
            await ctx.send(f"Welcome message added! Now have {len(self.welcome_messages)} messages.")
        else:
            await ctx.send("Failed to save welcome message.")
    
    @welcome.command(name="remove")
    async def welcome_remove(self, ctx, index: int):
        """
        Remove a welcome message
        
        Usage: !welcome remove <number>
        Example: !welcome remove 2
        """
        if index < 1 or index > len(self.welcome_messages):
            await ctx.send(f"Invalid index. Please specify a number between 1 and {len(self.welcome_messages)}.")
            return
            
        removed = self.welcome_messages.pop(index - 1)
        if self.save_messages():
            await ctx.send(f"Removed welcome message: `{removed}`")
        else:
            # Restore the message if save failed
            self.welcome_messages.insert(index - 1, removed)
            await ctx.send("Failed to remove welcome message.")
    
    @welcome.command(name="list")
    async def welcome_list(self, ctx):
        """
        List all welcome messages
        
        Usage: !welcome list
        """
        if not self.welcome_messages:
            await ctx.send("No welcome messages configured.")
            return
            
        # Create an embed with all welcome messages
        embed = discord.Embed(
            title="Welcome Messages",
            description="Here are the current welcome messages:",
            color=discord.Color.blue()
        )
        
        for i, message in enumerate(self.welcome_messages, 1):
            embed.add_field(name=f"Message {i}", value=message, inline=False)
            
        await ctx.send(embed=embed)
    
    @welcome.command(name="test")
    async def welcome_test(self, ctx):
        """
        Test welcome message
        
        Usage: !welcome test
        """
        if not self.welcome_messages:
            await ctx.send("No welcome messages configured.")
            return
            
        if not self.welcome_channel_id:
            await ctx.send("No welcome channel set. Please set a welcome channel first.")
            return
            
        welcome_channel = ctx.guild.get_channel(int(self.welcome_channel_id))
        if not welcome_channel:
            await ctx.send("Welcome channel not found. Please set a valid welcome channel.")
            return
            
        # Select a random welcome message
        message = random.choice(self.welcome_messages)
        
        # Format the message with user and server info
        message = message.replace("{user}", ctx.author.mention)
        message = message.replace("{server}", ctx.guild.name)
        message = message.replace("{username}", str(ctx.author))
        message = message.replace("{count}", str(ctx.guild.member_count))
        
        # Create an embed
        embed = discord.Embed(
            title="Welcome to the server! (TEST)",
            description=message,
            color=discord.Color.green()
        )
        
        # Add user avatar
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        
        # Add server icon if available
        if ctx.guild.icon:
            embed.set_footer(text=f"{ctx.guild.name} • Member #{ctx.guild.member_count}", icon_url=ctx.guild.icon.url)
        else:
            embed.set_footer(text=f"{ctx.guild.name} • Member #{ctx.guild.member_count}")
            
        await welcome_channel.send(embed=embed)
        await ctx.send(f"Test welcome message sent to {welcome_channel.mention}")
    
    @commands.group(name="goodbye", invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def goodbye(self, ctx):
        """
        Goodbye message commands
        
        Usage: !goodbye [set, add, remove, channel, test]
        """
        await ctx.send("Goodbye message commands:\n"
                     f"`{ctx.prefix}goodbye channel #channel` - Set goodbye channel\n"
                     f"`{ctx.prefix}goodbye add <message>` - Add a goodbye message\n"
                     f"`{ctx.prefix}goodbye remove <number>` - Remove a goodbye message\n"
                     f"`{ctx.prefix}goodbye list` - List all goodbye messages\n"
                     f"`{ctx.prefix}goodbye test` - Test goodbye message\n\n"
                     "Available placeholders: {user}, {server}, {username}, {count}")
    
    @goodbye.command(name="channel")
    async def goodbye_channel(self, ctx, channel: discord.TextChannel = None):
        """
        Set the goodbye message channel
        
        Usage: !goodbye channel #channel
        Example: !goodbye channel #goodbye
        """
        if channel is None:
            # Show current goodbye channel
            if self.goodbye_channel_id:
                current_channel = ctx.guild.get_channel(int(self.goodbye_channel_id))
                if current_channel:
                    await ctx.send(f"Current goodbye channel is: {current_channel.mention}")
                else:
                    await ctx.send(f"Current goodbye channel is set but not found: {self.goodbye_channel_id}")
            else:
                await ctx.send("No goodbye channel is set. Use this command with a channel mention to set one.")
            return
            
        # Set the goodbye channel
        self.goodbye_channel_id = str(channel.id)
        if self.save_messages():
            await ctx.send(f"Goodbye channel set to: {channel.mention}")
        else:
            await ctx.send("Failed to save goodbye channel.")
    
    @goodbye.command(name="add")
    async def goodbye_add(self, ctx, *, message: str):
        """
        Add a goodbye message
        
        Usage: !goodbye add <message>
        Example: !goodbye add Goodbye {user}! We'll miss you.
        """
        self.goodbye_messages.append(message)
        if self.save_messages():
            await ctx.send(f"Goodbye message added! Now have {len(self.goodbye_messages)} messages.")
        else:
            await ctx.send("Failed to save goodbye message.")
    
    @goodbye.command(name="remove")
    async def goodbye_remove(self, ctx, index: int):
        """
        Remove a goodbye message
        
        Usage: !goodbye remove <number>
        Example: !goodbye remove 2
        """
        if index < 1 or index > len(self.goodbye_messages):
            await ctx.send(f"Invalid index. Please specify a number between 1 and {len(self.goodbye_messages)}.")
            return
            
        removed = self.goodbye_messages.pop(index - 1)
        if self.save_messages():
            await ctx.send(f"Removed goodbye message: `{removed}`")
        else:
            # Restore the message if save failed
            self.goodbye_messages.insert(index - 1, removed)
            await ctx.send("Failed to remove goodbye message.")
    
    @goodbye.command(name="list")
    async def goodbye_list(self, ctx):
        """
        List all goodbye messages
        
        Usage: !goodbye list
        """
        if not self.goodbye_messages:
            await ctx.send("No goodbye messages configured.")
            return
            
        # Create an embed with all goodbye messages
        embed = discord.Embed(
            title="Goodbye Messages",
            description="Here are the current goodbye messages:",
            color=discord.Color.blue()
        )
        
        for i, message in enumerate(self.goodbye_messages, 1):
            embed.add_field(name=f"Message {i}", value=message, inline=False)
            
        await ctx.send(embed=embed)
    
    @goodbye.command(name="test")
    async def goodbye_test(self, ctx):
        """
        Test goodbye message
        
        Usage: !goodbye test
        """
        if not self.goodbye_messages:
            await ctx.send("No goodbye messages configured.")
            return
            
        if not self.goodbye_channel_id:
            await ctx.send("No goodbye channel set. Please set a goodbye channel first.")
            return
            
        goodbye_channel = ctx.guild.get_channel(int(self.goodbye_channel_id))
        if not goodbye_channel:
            await ctx.send("Goodbye channel not found. Please set a valid goodbye channel.")
            return
            
        # Select a random goodbye message
        message = random.choice(self.goodbye_messages)
        
        # Format the message with user and server info
        message = message.replace("{user}", str(ctx.author))
        message = message.replace("{server}", ctx.guild.name)
        message = message.replace("{username}", str(ctx.author))
        message = message.replace("{count}", str(ctx.guild.member_count))
        
        # Create an embed
        embed = discord.Embed(
            title="Member Left (TEST)",
            description=message,
            color=discord.Color.red()
        )
        
        # Add user avatar
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        
        # Add server icon if available
        if ctx.guild.icon:
            embed.set_footer(text=f"{ctx.guild.name} • Now {ctx.guild.member_count} members", icon_url=ctx.guild.icon.url)
        else:
            embed.set_footer(text=f"{ctx.guild.name} • Now {ctx.guild.member_count} members")
            
        await goodbye_channel.send(embed=embed)
        await ctx.send(f"Test goodbye message sent to {goodbye_channel.mention}")

async def setup(bot):
    await bot.add_cog(Events(bot)) 