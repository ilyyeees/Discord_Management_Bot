# G1 Admin - Discord Bot
## Made By Ilyes Abbas

G1 Admin is a feature-rich Discord bot designed for the ENSIA G1 server. It includes moderation tools, welcome/goodbye messages, interactive commands, and more.

## Features

- **Broadcast Functionality**: Send announcements to all server members via DM
- **Customizable Profile Picture**: Change the bot's avatar with a simple command
- **Moderation Tools**: Commands for muting, banning, kicking, and managing user roles
- **Welcome/Goodbye Messages**: Automatically greet new users and say goodbye when users leave
- **Logging System**: Log bot actions and server events to a designated channel
- **Customizable Prefix**: Change the command prefix to your preference
- **Interactive Commands**: Fun commands like polls, dice rolls, and 8-ball for engagement

## Setup

### Prerequisites

- Python 3.8 or higher
- A Discord bot token (see [Creating a Discord Bot](#creating-a-discord-bot))
- Discord Server with appropriate permissions

### Installation

1. Clone or download this repository
2. Install the required packages:

```bash
pip install -r requirements.txt
```

3. Set up your configuration:
   - Edit the `config.json` file that will be generated on first run
   - Add your bot token and customize other settings

4. Run the bot:

```bash
python bot.py
```

### Creating a Discord Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Navigate to the "Bot" tab and click "Add Bot"
4. Under the "TOKEN" section, click "Copy" to copy your bot token
5. Paste this token in your `config.json` file
6. In the "Bot" settings, enable the following Privileged Gateway Intents:
   - Presence Intent
   - Server Members Intent
   - Message Content Intent
7. To invite the bot to your server, go to the "OAuth2" tab, select "bot" under "SCOPES"
8. Select the necessary permissions and use the generated invite link

## Required Permissions

For full functionality, the bot needs the following permissions:

- Manage Server (for welcome/goodbye settings)
- Manage Roles (for moderation)
- Kick Members
- Ban Members
- Manage Messages
- Embed Links
- Attach Files
- Read Message History
- Add Reactions
- Use External Emojis
- Send Messages
- Read Messages/View Channels

## Hosting Options

### Local Hosting

- Suitable for testing or small servers
- The bot runs as long as your computer is on and the script is running
- Use a tool like [PM2](https://pm2.keymetrics.io/) to keep the bot running in the background

### Cloud Hosting

#### Heroku
1. Create a Heroku account and install the Heroku CLI
2. Initialize a git repository in your bot folder
3. Create a `Procfile` with the content: `worker: python bot.py`
4. Deploy to Heroku:

```bash
heroku login
heroku create your-bot-name
git add .
git commit -m "Initial commit"
heroku git:remote -a your-bot-name
git push heroku master
```

5. Set up your bot token as a config variable:

```bash
heroku config:set BOT_TOKEN=your_token_here
```

6. Start the worker:

```bash
heroku ps:scale worker=1
```

#### Railway.app
1. Create an account on [Railway](https://railway.app/)
2. Link your GitHub repository
3. Add environment variables for your bot token
4. Deploy from the dashboard

#### Oracle Cloud (Free Tier)
1. Create an Oracle Cloud account
2. Set up a free tier VM instance
3. Install Python and dependencies
4. Set up the bot to run on startup

## Commands

### General
- `!help` - Shows all available commands
- `!config` - Show current bot configuration

### Admin & Settings
- `!setprefix <prefix>` - Change the command prefix
- `!setpfp [URL]` - Change the bot's profile picture
- `!setlogchannel #channel` - Set the logging channel
- `!setadminrole @role` - Add an admin role
- `!removeadminrole @role` - Remove an admin role

### Broadcast
- `!broadcast <message>` - Send a message to all server members
- `!dmuser @user <message>` - Send a direct message to a specific user

### Moderation
- `!kick @user [reason]` - Kick a user from the server
- `!ban @user [reason]` - Ban a user from the server
- `!unban <user_id> [reason]` - Unban a user by ID
- `!mute @user [duration] [reason]` - Mute a user (timeout)
- `!unmute @user [reason]` - Unmute a user
- `!warn @user [reason]` - Warn a user
- `!purge <amount> [@user]` - Delete messages in a channel
- `!addrole @user @role` - Add a role to a user
- `!removerole @user @role` - Remove a role from a user

### Welcome/Goodbye
- `!welcome channel #channel` - Set welcome channel
- `!welcome add <message>` - Add a welcome message
- `!welcome remove <number>` - Remove a welcome message
- `!welcome list` - List all welcome messages
- `!welcome test` - Test welcome message
- `!goodbye channel #channel` - Set goodbye channel
- `!goodbye add <message>` - Add a goodbye message
- `!goodbye remove <number>` - Remove a goodbye message
- `!goodbye list` - List all goodbye messages
- `!goodbye test` - Test goodbye message

### Interactive
- `!poll "Question" "Option 1" "Option 2"...` - Create a poll
- `!endpoll [message_id]` - End a poll and show results
- `!roll [XdY]` - Roll dice (default: 1d6)
- `!choose "Option 1" "Option 2"...` - Choose between options
- `!8ball <question>` - Ask the magic 8-ball
- `!countdown [seconds] [event]` - Start a countdown timer
- `!quote <message_id>` - Quote a message

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues or questions, please contact Ilyes Abbas.

---

## Made By Ilyes Abbas | ENSIA G1 Admin Bot 