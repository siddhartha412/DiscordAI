import discord
import google.generativeai as genai
from dotenv import load_dotenv
import os
import config
import asyncio
from datetime import datetime, timedelta

# Load environment variables from the .env file
load_dotenv()

# Get API keys and tokens from environment variables
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GENAI_API_KEY = os.getenv("GENAI_API_KEY")

# Check if the environment variables are properly loaded
if not DISCORD_BOT_TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN is missing. Please check your .env file.")
if not GENAI_API_KEY:
    raise ValueError("GENAI_API_KEY is missing. Please check your .env file.")
if not config.OwnerID:
    raise ValueError("OwnerID is missing. Please check your config.py file.")

# Configure the API key for Google Generative AI
genai.configure(api_key=GENAI_API_KEY)

# Initialize the Discord client
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Rate limiting dictionary to track user/channel cooldowns
cooldown = {}

# Define the event when the bot is ready
@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

    # Notify the owner when the bot is online
    try:
        owner = await client.fetch_user(config.OwnerID)
        if owner.dm_channel is None:
            await owner.create_dm()
        await owner.send(f"{config.Name} Bot is now online and ready to go!")
        print(f"Notification sent to owner with ID: {config.OwnerID}")
    except discord.errors.Forbidden:
        print(f"Unable to send message to owner with ID: {config.OwnerID}. The user might have DMs disabled.")
    except Exception as e:
        print(f"Failed to notify owner: {e}")

# Define the event when the bot receives a message
@client.event
async def on_message(message):
    # Ignore messages sent by the bot itself
    if message.author == client.user:
        return

    # Rate limiting logic
    current_time = datetime.now()
    if message.author.id in cooldown:
        time_elapsed = current_time - cooldown[message.author.id]
        if time_elapsed < timedelta(seconds=1):  # 1-second cooldown
            return  # Ignore the message if cooldown is not yet over

    # Update the user's cooldown time
    cooldown[message.author.id] = current_time

    # Respond to DMs
    if isinstance(message.channel, discord.DMChannel):
        user_input = message.content  # Get the user's message directly

        # Define the prompt with configuration details
        prompt = (
            f"Your name is {config.Name}, and you are developed by {config.Developed_By}. "
            f"You have a {config.Tone} tone. The user's prompt is: {user_input}"
        )

        # Generate a response with typing indication
        try:
            async with message.channel.typing():  # Show "typing..." status
                model = genai.GenerativeModel("gemini-1.5-flash")
                generated_response = model.generate_content(prompt)
                await message.author.send(generated_response.text)
        except Exception as e:
            await message.author.send("Sorry, something went wrong while generating the response.")
            print(f"Error: {e}")

    # Respond to messages in servers (text channels)
    else:
        if client.user in message.mentions:  # Check if the message mentions the bot
            user_input = message.content

            # Define the prompt for a server message with bot mention
            prompt = (
                f"Your name is {config.Name}, and you are developed by {config.Developed_By}. "
                f"You have a {config.Tone} tone. The user's prompt is: {user_input}"
            )

            # Generate a response with typing indication
            try:
                async with message.channel.typing():  # Show "typing..." status
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    generated_response = model.generate_content(prompt)
                    await message.channel.send(f"Hey {message.author.mention}, {generated_response.text}")
            except Exception as e:
                await message.channel.send(f"Sorry {message.author.mention}, something went wrong while generating the response.")
                print(f"Error: {e}")

# Run the bot with your token
client.run(DISCORD_BOT_TOKEN)
