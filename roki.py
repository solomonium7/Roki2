import discord
from discord.ext import commands
import json
import os

# Load environment variables
TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
MOD_CHANNEL_ID = int(os.getenv("MOD_CHANNEL_ID"))  # Channel for mod review
TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID"))  # Reaction trigger channel
ALLOWED_ROLE_ID = int(os.getenv("ALLOWED_ROLE_ID"))  # Role allowed to approve/promote

# Load or initialize user data
USER_DATA_FILE = "user_progress.json"
if os.path.exists(USER_DATA_FILE):
    with open(USER_DATA_FILE, "r") as f:
        user_data = json.load(f)
else:
    user_data = {}

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# Save user progress function
def save_data():
    with open(USER_DATA_FILE, "w") as f:
        json.dump(user_data, f, indent=4)

# Modules and their corresponding questions
modules = {
    1: "Read the following theory: [📖 The Crisis of Humanity](https://discord.com/channels/1342982226916409354/1343626603682463796). Once you have read, answer this: How does the Fermi Paradox serve as a warning to Humanity? What are the greatest threats to Humanity's survival?",
    2: "Read the following theory: [📖 Material Truth vs. Strategic Reality](https://discord.com/channels/1342982226916409354/1343626603682463796). Once you have read, answer this: Why do humans live in conflicting realities? How does Strategic Reality shape the way people see the world, and why does Humanity need One Truth?",
    3: "Read the following theory: [📖 Individual Action](https://discord.com/channels/1342982226916409354/1345134323397034014). Once you have read, answer this: If Humanity is an organism, what is the role of the individual within it? How does the ‘self’ (sam/сам) bridge the gap between theory and action?",
    4: "Read the following theory: [📖 The Triune Structure of Human Truth](https://discord.com/channels/1342982226916409354/1345135557092835389). Once you have read, answer this: Explain how Perception, Values, and Purpose shape Strategic Reality. How should the Human Truth be structured to align Humanity with its survival? Why is it necessary to develop a universal set of values based on material reality?"
}

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")

@bot.command()
@commands.has_permissions(administrator=True)
async def send_course_message(ctx):
    """Send a message for users to react and start Module 1"""
    message = await ctx.send("React to this message to start ideological education!")
    with open("message_id.txt", "w") as f:
        f.write(str(message.id))  # Save message ID
    await message.add_reaction("✅")  # Add reaction automatically

@bot.event
async def on_raw_reaction_add(payload):
    """Handle reaction to start module 1"""
    if payload.user_id == bot.user.id:
        return
    
    try:
        with open("message_id.txt", "r") as f:
            stored_message_id = int(f.read().strip())
    except FileNotFoundError:
        print("No stored message ID found, ignoring reaction.")
        return

    if payload.message_id == stored_message_id:
        guild = bot.get_guild(payload.guild_id)
        user = guild.get_member(payload.user_id)
        if user and not user.bot:
            user_data[str(user.id)] = 1  # Assign first module
            save_data()
            try:
                dm = await user.create_dm()
                await dm.send(f"✅ Welcome to ideological education!\n{modules[1]}\n\n📨 Reply with your answer.")
            except discord.Forbidden:
                print(f"Cannot DM {user.name}, they might have DMs off.")

@bot.event
async def on_message(message):
    """Capture user's DM response and forward it to mod review"""
    if message.guild is None and not message.author.bot:
        user_id = str(message.author.id)
        if user_id in user_data:
            stage = user_data[user_id]
            mod_channel = bot.get_channel(MOD_CHANNEL_ID)

            await mod_channel.send(f"📢 **New submission from {message.author.mention}**\n📖 **Stage {stage}:** {message.content}")

            await message.author.send("✅ Your answer has been submitted for review. You will be notified if it is approved or if you need to revise it.")
        else:
            await message.author.send("❌ You haven't started the ideological education yet. React to the start message first!")

    await bot.process_commands(message)

@bot.command()
async def promote(ctx, member: discord.Member):
    """Approve a user's response and move them to the next module"""
    if not discord.utils.get(ctx.author.roles, id=ALLOWED_ROLE_ID):
        await ctx.send(f"{ctx.author.mention}, you do not have permission to use this command.")
        return

    user_id = str(member.id)
    if user_id in user_data:
        current_stage = user_data[user_id]

        if current_stage < len(modules):
            next_stage = current_stage + 1
            user_data[user_id] = next_stage
            save_data()
            await member.send(f"✅ Your answer was approved!\n📖 Here is your next lesson:\n\n{modules[next_stage]}")
            await ctx.send(f"{member.mention} has been promoted to Stage {next_stage}.")
        else:
            await ctx.send(f"{member.mention} has completed all modules.")
    else:
        await ctx.send(f"{member.mention} has not started the course yet.")

@bot.command()
async def reject(ctx, member: discord.Member, *, feedback: str):
    """Reject a user's response and provide feedback"""
    if not discord.utils.get(ctx.author.roles, id=ALLOWED_ROLE_ID):
        await ctx.send(f"{ctx.author.mention}, you do not have permission to use this command.")
        return

    try:
        await member.send(f"❌ Your submission was rejected.\n📝 Feedback: {feedback}\n🔄 Try again with a revised answer.")
        await ctx.send(f"Feedback sent to {member.mention}.")
    except discord.Forbidden:
        await ctx.send(f"Could not send feedback to {member.mention}. They may have DMs disabled.")

@bot.command()
async def progress(ctx, member: discord.Member = None):
    """Check a user's progress"""
    member = member or ctx.author  # If no member is specified, check command issuer
    user_id = str(member.id)

    if user_id in user_data:
        stage = user_data[user_id]
        await ctx.send(f"📊 **{member.name}'s Progress:** Stage {stage}")
    else:
        await ctx.send(f"❌ {member.name} has not started the ideological education.")

bot.run(TOKEN)
