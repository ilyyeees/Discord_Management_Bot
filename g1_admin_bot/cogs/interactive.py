import discord
from discord.ext import commands
import logging
import asyncio
import random
import datetime

logger = logging.getLogger("g1_admin.interactive")

class Interactive(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_polls = {}
        
    @commands.command(name="poll")
    @commands.has_permissions(manage_messages=True)
    async def create_poll(self, ctx, question: str, *options):
        """
        Create a poll with reactions for voting
        
        Usage: !poll "Question" "Option 1" "Option 2" "Option 3"...
        Example: !poll "What's your favorite color?" "Red" "Blue" "Green"
        
        Note: Up to 10 options can be provided
        """
        if len(options) < 2:
            await ctx.send("Please provide at least 2 options for the poll.")
            return
            
        if len(options) > 10:
            await ctx.send("You can only have up to 10 options in a poll.")
            return
            
        # Emoji options for polls
        emoji_options = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        
        # Create poll embed
        embed = discord.Embed(
            title=f"📊 Poll: {question}",
            description="React with the corresponding emoji to vote!",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )
        
        # Add options to embed
        options_text = ""
        for i, option in enumerate(options):
            options_text += f"{emoji_options[i]} {option}\n\n"
            
        embed.add_field(name="Options", value=options_text, inline=False)
        embed.set_footer(text=f"Poll created by {ctx.author}")
        
        # Send poll message
        poll_message = await ctx.send(embed=embed)
        
        # Add reaction options
        for i in range(len(options)):
            await poll_message.add_reaction(emoji_options[i])
            
        # Store active poll
        self.active_polls[poll_message.id] = {
            'question': question,
            'options': options,
            'created_by': ctx.author.id,
            'created_at': datetime.datetime.now(),
            'message_id': poll_message.id,
            'channel_id': ctx.channel.id
        }
    
    @commands.command(name="endpoll")
    @commands.has_permissions(manage_messages=True)
    async def end_poll(self, ctx, message_id: int = None):
        """
        End a poll and display results
        
        Usage: !endpoll [message_id]
        Example: !endpoll 123456789012345678
        
        If no message ID is provided, looks for the most recent poll in the channel
        """
        # If no message ID provided, try to find most recent poll in channel
        if message_id is None:
            for poll_id, poll_data in self.active_polls.items():
                if poll_data['channel_id'] == ctx.channel.id:
                    message_id = poll_id
                    break
                    
            if message_id is None:
                await ctx.send("No active polls found in this channel. Please provide a poll message ID.")
                return
                
        # Check if poll exists
        if message_id not in self.active_polls:
            await ctx.send("No active poll found with that message ID.")
            return
            
        poll_data = self.active_polls[message_id]
        
        # Only allow poll creator or admins to end polls
        if not (ctx.author.id == poll_data['created_by'] or ctx.author.guild_permissions.administrator):
            await ctx.send("Only the poll creator or administrators can end this poll.")
            return
            
        try:
            # Get poll message
            channel = self.bot.get_channel(poll_data['channel_id'])
            if not channel:
                await ctx.send("Could not find the channel where the poll was created.")
                return
                
            poll_message = await channel.fetch_message(message_id)
            
            # Emoji options for polls
            emoji_options = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
            
            # Count votes
            results = []
            total_votes = 0
            
            for i, option in enumerate(poll_data['options']):
                if i >= len(emoji_options):
                    break
                    
                reaction = discord.utils.get(poll_message.reactions, emoji=emoji_options[i])
                count = 0
                if reaction:
                    count = reaction.count - 1  # Subtract 1 for the bot's reaction
                    if count < 0:
                        count = 0
                        
                results.append((option, count))
                total_votes += count
                
            # Create results embed
            embed = discord.Embed(
                title=f"📊 Poll Results: {poll_data['question']}",
                color=discord.Color.gold(),
                timestamp=datetime.datetime.now()
            )
            
            # Sort results by vote count (descending)
            results.sort(key=lambda x: x[1], reverse=True)
            
            # Add results to embed
            results_text = ""
            for option, count in results:
                percentage = 0
                if total_votes > 0:
                    percentage = (count / total_votes) * 100
                    
                results_text += f"**{option}**: {count} votes ({percentage:.1f}%)\n\n"
                
            embed.add_field(name=f"Results (Total Votes: {total_votes})", value=results_text, inline=False)
            embed.set_footer(text=f"Poll ended by {ctx.author}")
            
            # Send results
            await ctx.send(embed=embed)
            
            # Mark poll as ended by editing original message
            original_embed = poll_message.embeds[0]
            original_embed.title = f"📊 Poll Ended: {poll_data['question']}"
            original_embed.set_footer(text=f"Poll ended by {ctx.author}")
            await poll_message.edit(embed=original_embed)
            
            # Remove from active polls
            del self.active_polls[message_id]
            
        except discord.NotFound:
            await ctx.send("Could not find the poll message. It may have been deleted.")
            del self.active_polls[message_id]
        except Exception as e:
            logger.error(f"Error ending poll: {e}")
            await ctx.send(f"An error occurred: {e}")
    
    @commands.command(name="roll")
    async def roll_dice(self, ctx, dice: str = "1d6"):
        """
        Roll dice using the XdY format
        
        Usage: !roll [XdY]
        Example: !roll 2d20
        
        Default is 1d6 (one six-sided die)
        """
        try:
            # Parse dice format
            if 'd' not in dice:
                await ctx.send("Invalid format. Use XdY format, e.g., 2d6.")
                return
                
            num_dice, num_sides = map(int, dice.split('d'))
            
            if num_dice <= 0 or num_sides <= 0:
                await ctx.send("Number of dice and sides must be positive numbers.")
                return
                
            if num_dice > 100:
                await ctx.send("You can roll a maximum of 100 dice at once.")
                return
                
            # Roll the dice
            results = [random.randint(1, num_sides) for _ in range(num_dice)]
            total = sum(results)
            
            # Create response
            if num_dice == 1:
                await ctx.send(f"🎲 {ctx.author.mention} rolled a {total}")
            else:
                rolls_text = ', '.join(str(r) for r in results)
                await ctx.send(f"🎲 {ctx.author.mention} rolled {num_dice}d{num_sides}: {rolls_text} = **{total}**")
        
        except ValueError:
            await ctx.send("Invalid format. Use XdY format, e.g., 2d6.")
        except Exception as e:
            logger.error(f"Error in roll command: {e}")
            await ctx.send(f"An error occurred: {e}")
    
    @commands.command(name="choose")
    async def choose(self, ctx, *options):
        """
        Randomly choose between several options
        
        Usage: !choose "Option 1" "Option 2" "Option 3"...
        Example: !choose "Pizza" "Burger" "Tacos"
        """
        if len(options) < 2:
            await ctx.send("Please provide at least 2 options to choose from.")
            return
            
        # Choose a random option
        choice = random.choice(options)
        
        # Build suspense with typing
        async with ctx.typing():
            await asyncio.sleep(1.5)
            
        # Send response
        await ctx.send(f"🤔 {ctx.author.mention}, I choose... **{choice}**!")
    
    @commands.command(name="8ball")
    async def magic_8ball(self, ctx, *, question: str):
        """
        Ask the magic 8-ball a question
        
        Usage: !8ball <question>
        Example: !8ball Will I win the lottery?
        """
        # List of 8-ball responses
        responses = [
            # Positive
            "It is certain.",
            "It is decidedly so.",
            "Without a doubt.",
            "Yes, definitely.",
            "You may rely on it.",
            "As I see it, yes.",
            "Most likely.",
            "Outlook good.",
            "Yes.",
            "Signs point to yes.",
            # Neutral
            "Reply hazy, try again.",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again.",
            # Negative
            "Don't count on it.",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good.",
            "Very doubtful."
        ]
        
        # Choose a random response
        response = random.choice(responses)
        
        # Build suspense with typing
        async with ctx.typing():
            await asyncio.sleep(2)
            
        # Create an embed
        embed = discord.Embed(
            title="🎱 Magic 8-Ball",
            color=discord.Color.purple()
        )
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=response, inline=False)
        embed.set_footer(text=f"Asked by {ctx.author}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="countdown")
    @commands.has_permissions(manage_messages=True)
    async def countdown(self, ctx, seconds: int = 10, *, event: str = "Countdown"):
        """
        Start a countdown timer
        
        Usage: !countdown [seconds] [event name]
        Example: !countdown 30 Meeting start
        
        Default is 10 seconds
        """
        if seconds <= 0:
            await ctx.send("Please provide a positive number of seconds.")
            return
            
        if seconds > 300:
            await ctx.send("Maximum countdown time is 300 seconds (5 minutes).")
            return
            
        # Create initial countdown message
        embed = discord.Embed(
            title=f"⏳ {event}",
            description=f"Time remaining: {seconds} seconds",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Countdown started by {ctx.author}")
        
        countdown_msg = await ctx.send(embed=embed)
        
        # Update countdown every second
        while seconds > 0:
            await asyncio.sleep(1)
            seconds -= 1
            
            # Update every 5 seconds or for the final 5 seconds
            if seconds % 5 == 0 or seconds < 5:
                embed.description = f"Time remaining: {seconds} seconds"
                
                # Change color for last 5 seconds
                if seconds <= 5:
                    embed.color = discord.Color.red()
                    
                await countdown_msg.edit(embed=embed)
                
        # Final message
        embed = discord.Embed(
            title=f"🔔 {event}",
            description="Time's up!",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Countdown started by {ctx.author}")
        
        await countdown_msg.edit(embed=embed)
        await ctx.send(f"🔔 **{event}** - Time's up! {ctx.author.mention}")
    
    @commands.command(name="quote")
    async def quote_message(self, ctx, message_id: int):
        """
        Quote a message from the current channel
        
        Usage: !quote <message_id>
        Example: !quote 123456789012345678
        """
        try:
            # Try to fetch the message
            message = await ctx.channel.fetch_message(message_id)
            
            # Create embed
            embed = discord.Embed(
                description=message.content,
                color=discord.Color.light_grey(),
                timestamp=message.created_at
            )
            
            # Add author info
            embed.set_author(
                name=message.author.display_name,
                icon_url=message.author.display_avatar.url
            )
            
            # Add message link
            embed.add_field(name="Source", value=f"[Jump to message]({message.jump_url})", inline=False)
            
            # Add attachments if any
            if message.attachments:
                if message.attachments[0].url.lower().endswith(('png', 'jpeg', 'jpg', 'gif', 'webp')):
                    embed.set_image(url=message.attachments[0].url)
                else:
                    embed.add_field(name="Attachment", value=f"[View attachment]({message.attachments[0].url})", inline=False)
                    
            # Set footer
            embed.set_footer(text=f"Quoted by {ctx.author.display_name}")
            
            await ctx.send(embed=embed)
            
        except discord.NotFound:
            await ctx.send("Message not found. Make sure you're using the correct message ID.")
        except Exception as e:
            logger.error(f"Error quoting message: {e}")
            await ctx.send(f"An error occurred: {e}")

async def setup(bot):
    await bot.add_cog(Interactive(bot)) 