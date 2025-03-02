import discord
from discord.ext import commands
import json
import os

TOKEN = "YOUR_BOT_TOKEN"  # Replace with your actual bot token
GUILD_ID = 123456789  # Replace with your server ID
MOD_CHANNEL_ID = 123456789  # Replace with your mod channel ID
TARGET_CHANNEL_ID = 123456789  # Channel where reactions trigger bot

# Load or initialize user data
USER_DATA_FILE = "user_progress.json"
if os.path.exists(USER_DATA_FILE):
    with open(USER_DATA_FILE, "r") as f:
        user_data = json.load(f)
else:
    user_data = {}

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# Save user progress

def save_data():
    with open(USER_DATA_FILE, "w") as f:
        json.dump(user_data, f, indent=4)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return
    if reaction.message.channel.id == TARGET_CHANNEL_ID:
        user_data[str(user.id)] = 1  # Start at Module 1
        save_data()
        try:
            await user.send("Hi! Here is Course Material for Module 1.\nRespond to me with an answer to the following question: [QUESTION]")
        except discord.Forbidden:
            print(f"Can't DM {user.name}, they might have DMs off.")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)
    if isinstance(message.channel, discord.DMChannel) and user_id in user_data:
        mod_channel = bot.get_channel(MOD_CHANNEL_ID)
        if mod_channel:
            forwarded_message = await mod_channel.send(f"User {message.author.mention} (Stage {user_data[user_id]}) responded: {message.content}")
            user_data[user_id] = user_data.get(user_id, 1)  # Ensure they exist in data
            save_data()
            await message.author.send("Your response has been forwarded to the Ideological Education Committee.")

            # Store message ID for reply tracking
            user_data[f"msg_{forwarded_message.id}"] = user_id
            save_data()
        else:
            print("Mod channel not found!")
    await bot.process_commands(message)

@bot.event
async def on_message_edit(before, after):
    await on_message(after)  # Handle edited messages like new messages

@bot.event
async def on_message_delete(message):
    if message.channel.id == MOD_CHANNEL_ID:
        msg_id = str(message.id)
        if msg_id in user_data:
            del user_data[msg_id]
            save_data()

@bot.command()
@commands.has_permissions(administrator=True)
async def promote(ctx, member: discord.Member, stage: int):
    """Promote a user to the next module."""
    user_id = str(member.id)
    if user_id in user_data:
        user_data[user_id] = stage
        save_data()
        await member.send(f"Congratulations! You have been promoted to Stage {stage}. Here is your new module.")
        await ctx.send(f"{member.mention} has been promoted to Stage {stage}.")
    else:
        await ctx.send(f"{member.mention} has not started the course yet.")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id == MOD_CHANNEL_ID and message.reference:
        original_message = await message.channel.fetch_message(message.reference.message_id)
        if original_message:
            user_id = user_data.get(f"msg_{original_message.id}")
            if user_id:
                user = bot.get_user(int(user_id))
                if user:
                    await user.send(f"The committee has responded: {message.content}")

    await bot.process_commands(message)

bot.run(TOKEN)
