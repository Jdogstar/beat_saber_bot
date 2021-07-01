"""Runs and holds the bot."""

import os
from datetime import datetime
import re
from urllib.request import urlopen, Request
from asyncio.proactor_events import _ProactorBasePipeTransport
import platform
from functools import wraps
import discord
from dotenv import load_dotenv

# Loading needed constants that have to be secured elsewhere,
# else people can use your discord token to mess with your bot.
# I prefer using a .env file holding them.
load_dotenv("bot.env")
TOKEN = os.getenv('DISCORD_TOKEN')  # Bot ID
CHANNEL = int(os.getenv('DISCORD_CHANNEL'))  # Channel ID


# Main bot
class MyClient(discord.Client):
    """Client Class.

    Class to hold the client information for the bot."""
    # Initialize bot along with a background task
    def __init__(self, *args, **kwargs):
        """Constructor for the bot.

        Args:
            *args, **kwargs: placeholders for arguments"""
        super().__init__(*args, **kwargs)
        # Create the background task and run it in the background

    # Confirm the bot connects to the server
    async def on_ready(self):
        """Function to test if the bot is connected to the Discord API.

            It runs the necessary channel logic to ensure it controls
            the channel exclusively, on top of checking if it is the correct
            time to send a new update (on a new day).

            Returns:
                None"""
        try:
            # If the server has no message in the desired channel,
            # it places is one there.
            channel = self.get_channel(CHANNEL)
            messages = await channel.history(limit=1).flatten()
            if not messages:
                await self.get_status_bmfb()
            else:
                async for message in channel.history():
                    # Ensure all messages are only from itself
                    if message.author != self.user:
                        await message.delete()
                    # If it encounters a message from itself, it's cleaned up.
                    # it is now allowed to stop checking messages.
                    if message.author == self.user:
                        break
                # Checks if the last message from the bot was on the same day.
                # If so, do not resend status, else resend status
                last_message_lst = await channel.history(limit=1).flatten()
                last_msg = last_message_lst[0].created_at.strftime('%Y-%m-%d')
                current_date = datetime.today().strftime('%Y-%m-%d')
                if last_msg != current_date:
                    await self.get_status_bmfb()
                else:
                    print('Logged in as')
                    print(self.user.name)
                    print(self.user.id)
                    print('------')
                    print("You already got an update today")
        except discord.HTTPException:  # discord.NotFound:
            print("Something went wrong with the http", file="error.txt")
        # Kills the client connection so the program can exit swiftly
        self.loop.stop()

    async def get_status_bmfb(self):
        """Checks the html for the lastest version of beat saber mod"""
        channel = self.get_channel(CHANNEL)
        # Current beat saber version as of 6/30/2021
        update_pat = re.compile(r'1.16')

        # Get the html from the site
        with urlopen(Request("https://bmbf.dev/stable",
                             headers={"User-Agent": "Mozilla/5.0"})) as site:
            response_content = site.read().decode('utf-8')

            # See if there is a match, if so tell the channel
            # Else tell them there is no update
            matcher = re.search(update_pat, response_content)
        if matcher:
            await channel.send("Ayooo potential update to beat saber."
                               + "\nGo check!")
            await channel.send("https://bmbf.dev/stable")
        else:
            await channel.send("Nothing today sadly.")


def silence(func):
    """Imma going to be frank, this is code I lifted and "modified"
    off of a github inorder to fix an annoying windows quirk where
    asyncio throws a runtime error at the program's end for no
    conceivable reason."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except RuntimeError as error:
            if str(error) != 'Event loop is closed':
                raise
        return None
    return wrapper


# Setup instance of the bot and run the bot via the client
client = MyClient()
client.run(TOKEN)
if platform.system() == 'Windows':
    # Silence the exception here.
    _ProactorBasePipeTransport.__del__ = silence(
        _ProactorBasePipeTransport.__del__)
