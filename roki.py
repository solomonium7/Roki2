import discord
from discord.ext import commands
import json
import os

TOKEN = os.getenv("TOKEN")
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

# Command to send the reaction message and store its ID
@bot.command()
@commands.has_permissions(administrator=True)
async def send_course_message(ctx):
    message = await ctx.send("React to this message to start Module 1!")
    with open("message_id.txt", "w") as f:
        f.write(str(message.id))  # Save the message ID in a file
    await message.add_reaction("✅")  # Add a reaction automatically

# Reaction handler that checks for the stored message ID
@bot.event
async def on_reaction_add(reaction, user):
    print(f"Reaction detected: {reaction.emoji} from {user.name} on message {reaction.message.id} in {reaction.message.channel.name}")
    
    if user.bot:
        return
    
    try:
        with open("message_id.txt", "r") as f:
            stored_message_id = int(f.read().strip())
    except FileNotFoundError:
        print("No stored message ID found, ignoring reaction.")
        return
    
    if reaction.message.id == stored_message_id:  # Only trigger on the correct message
        print(f"Valid reaction on the correct message by {user.name}")
        
        user_data[str(user.id)] = 1  # Start at Module 1
        save_data()

        try:
            await user.send("Hi! Here is Course Material for Module 1.\nRespond to me with an answer to the following question: [QUESTION]")
            print(f"DM sent to {user.name}")
        except discord.Forbidden:
            print(f"Can't DM {user.name}, they might have DMs off.")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    print(f"Message detected from {message.author.name} in {message.channel}")
    
    user_id = str(message.author.id)
    if isinstance(message.channel, discord.DMChannel) and user_id in user_data:
        mod_channel = bot.get_channel(MOD_CHANNEL_ID)
        
        if mod_channel:
            print(f"Forwarding message to mod channel: {MOD_CHANNEL_ID}")
            forwarded_message = await mod_channel.send(
                f"User {message.author.mention} (Stage {user_data[user_id]}) responded: {message.content}"
            )

            user_data[f"msg_{forwarded_message.id}"] = user_id  # Track message for replies
            save_data()

            await message.author.send("Your response has been forwarded to the Ideological Education Committee.")
            print(f"Message forwarded successfully!")
        else:
            print("Mod channel not found!")
    else:
        print("Message not in DM or user not registered.")

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

    if isinstance(message.channel, discord.DMChannel):
        mod_channel = bot.get_channel(MOD_CHANNEL_ID)
        if mod_channel:
            await mod_channel.send(f"{message.author.mention} said: {message.content}")
            print(f"Message forwarded to mod channel: {MOD_CHANNEL_ID}")
    
    await bot.process_commands(message)

bot.run(TOKEN)
