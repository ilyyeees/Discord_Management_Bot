import os
import discord
from discord.ext import commands
import asyncio
import logging
import json
import sys
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Bot author information
BOT_AUTHOR = "Made By Ilyes Abbas"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("g1_admin")

# Load configuration
def load_config():
    try:
        # First check for config file
        if os.path.exists('config.json'):
            with open('config.json', 'r') as f:
                config = json.load(f)
                
            # Check for token in environment first (env var overrides config file)
            if os.getenv("BOT_TOKEN"):
                config["token"] = os.getenv("BOT_TOKEN")
                
            return config
        else:
            # Default configuration
            config = {
                "token": os.getenv("BOT_TOKEN", ""),  # Get from environment or empty string
                "prefix": os.getenv("PREFIX", "!"),   # Get from environment or default to !
                "log_channel_id": os.getenv("LOG_CHANNEL_ID"),
                "admin_role_ids": [],
                "mod_role_ids": [],
                "bot_author": BOT_AUTHOR
            }
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=4)
            logger.warning("Config file created. Please fill in your bot token and other settings.")
            return config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {
            "token": os.getenv("BOT_TOKEN", ""),
            "prefix": os.getenv("PREFIX", "!"),
            "log_channel_id": os.getenv("LOG_CHANNEL_ID"),
            "admin_role_ids": [],
            "mod_role_ids": [],
            "bot_author": BOT_AUTHOR
        }

config = load_config()

# Define bot intents
intents = discord.Intents.default()
intents.members = True  # For welcome messages and member tracking
intents.message_content = True  # For command handling

# Initialize bot with specified prefix and intents
bot = commands.Bot(command_prefix=config.get("prefix", "!"), intents=intents)
bot.author = BOT_AUTHOR

# Bot events
@bot.event
async def on_ready():
    logger.info(f'{bot.user.name} has connected to Discord!')
    await bot.change_presence(activity=discord.Game(name=f"{config.get('prefix', '!')}help | {BOT_AUTHOR}"))
    
    # Log to log channel if configured
    if config.get("log_channel_id"):
        try:
            log_channel = bot.get_channel(int(config.get("log_channel_id")))
            if log_channel:
                embed = discord.Embed(
                    title=f"✅ {bot.user.name} is now online!",
                    description="Bot has successfully connected to Discord.",
                    color=discord.Color.green()
                )
                embed.set_footer(text=BOT_AUTHOR)
                await log_channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to send startup message to log channel: {e}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required argument. Please check `{config.get('prefix', '!')}help {ctx.command.name}`")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")
    else:
        logger.error(f"Command error: {error}")
        await ctx.send(f"An error occurred: {error}")
        
        # Log to log channel if configured
        if config.get("log_channel_id"):
            try:
                log_channel = bot.get_channel(int(config.get("log_channel_id")))
                if log_channel:
                    error_embed = discord.Embed(
                        title=f"⚠️ Error: Command `{ctx.command.name}` failed",
                        description=f"```{error}```",
                        color=discord.Color.red()
                    )
                    error_embed.set_footer(text=BOT_AUTHOR)
                    await log_channel.send(embed=error_embed)
            except Exception as e:
                logger.error(f"Failed to log error to channel: {e}")

# Modify help command to include author info
class CustomHelpCommand(commands.DefaultHelpCommand):
    async def send_bot_help(self, mapping):
        ctx = self.context
        destination = ctx.author if self.dm_help else ctx
        
        embed = discord.Embed(
            title="G1 Admin Bot Help",
            description="Here are all available commands:",
            color=discord.Color.blue()
        )
        
        for cog, commands in mapping.items():
            name = getattr(cog, "qualified_name", "No Category")
            filtered = await self.filter_commands(commands, sort=True)
            if filtered:
                value = "\n".join(f"`{c.name}` - {c.short_doc}" for c in filtered)
                embed.add_field(name=name, value=value, inline=False)
                
        embed.set_footer(text=BOT_AUTHOR)
        await destination.send(embed=embed)
        
    async def send_command_help(self, command):
        embed = discord.Embed(
            title=f"Command: {command.name}",
            description=command.help or "No description available.",
            color=discord.Color.blue()
        )
        
        if command.aliases:
            embed.add_field(name="Aliases", value=", ".join(command.aliases), inline=False)
            
        embed.add_field(name="Usage", value=f"`{self.get_command_signature(command)}`", inline=False)
        embed.set_footer(text=BOT_AUTHOR)
        
        destination = self.get_destination()
        await destination.send(embed=embed)

# Set custom help command
bot.help_command = CustomHelpCommand()

# Load all cogs
async def load_extensions():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                logger.info(f'Loaded extension: {filename[:-3]}')
            except Exception as e:
                logger.error(f'Failed to load extension {filename}: {e}')

async def main():
    async with bot:
        await load_extensions()
        await bot.start(config["token"])

# Run the bot
if __name__ == "__main__":
    if not config.get("token"):
        logger.error("Bot token not found in config.json or environment variables. Please add your token and restart the bot.")
        sys.exit(1)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown initiated by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}") 