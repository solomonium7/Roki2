import discord
from discord.ext import commands
import json
import os

TOKEN = os.getenv("TOKEN")
GUILD_ID = 1342982226916409354  # Replace with your server ID
MOD_CHANNEL_ID = 1345329325666205696  # Replace with your mod channel ID
TARGET_CHANNEL_ID = 1343517836391219221  # Channel where reactions trigger bot
ALLOWED_ROLE_ID = 1342997555612614747  # Replace with the role ID that can use !promote

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

@bot.command()
async def promote(ctx, member: discord.Member, stage: int):
    """Promote a user to the next module, only if the command issuer has a specific role."""
    allowed_role = discord.utils.get(ctx.author.roles, id=ALLOWED_ROLE_ID)
    if not allowed_role:
        await ctx.send(f"{ctx.author.mention}, you do not have permission to use this command.")
        print(f"Promotion attempt denied for {ctx.author.name} - insufficient role.")
        return
    
    user_id = str(member.id)
    print(f"Attempting to promote {member.name} (ID: {user_id}) to Stage {stage}")
    if user_id in user_data:
        user_data[user_id] = stage
        save_data()
        try:
            await member.send(f"Congratulations! You have been promoted to Stage {stage}. Here is your new module.")
            print(f"DM sent to {member.name} about promotion.")
        except discord.Forbidden:
            print(f"Cannot DM {member.name}, they might have DMs off.")
        await ctx.send(f"{member.mention} has been promoted to Stage {stage}.")
        print(f"{member.name} promoted to Stage {stage}")
    else:
        await ctx.send(f"{member.mention} has not started the course yet.")
        print(f"Promotion failed: {member.name} not found in user_data")

# Command for moderators to send a response to a user
@bot.command()
async def respond(ctx, member: discord.Member, *, message: str):
    """Allows moderators to respond to a user's inquiry."""
    if not discord.utils.get(ctx.author.roles, id=ALLOWED_ROLE_ID):
        await ctx.send(f"{ctx.author.mention}, you do not have permission to use this command.")
        print(f"Respond attempt denied for {ctx.author.name} - insufficient role.")
        return
    
    try:
        await member.send(f"The committee has responded: {message}")
        await ctx.send(f"Response sent to {member.mention}.")
        print(f"Response sent to {member.name}: {message}")
    except discord.Forbidden:
        print(f"Cannot DM {member.name}, they might have DMs off.")
        await ctx.send(f"Could not send a response to {member.mention}. They may have DMs disabled.")

bot.run(TOKEN)
