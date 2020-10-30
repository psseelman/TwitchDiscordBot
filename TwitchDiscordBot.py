import os
from twitchio.ext import commands
import twitchio
import discord
import asyncio
import nest_asyncio
import datetime
import re

# Twitch client init
twitch = commands.Bot(
    irc_token=os.environ['TWITCH_TMI_TOKEN'],
    client_id=os.environ['TWITCH_CLIENT_ID'],
    nick=os.environ['TWITCH_BOT_NICK'],
    prefix=os.environ['TWITCH_BOT_PREFIX'],
    initial_channels=["#" + os.environ['TWITCH_CHANNEL_NAME']]
)

last_ctx: twitchio.dataclasses.Context
command_list: list = ["!timestamp", "!clip", "!commands"]
bot_list: list = ["streamelements", "nightbot", "internationalbot"]
super_users_list: list = ["sisyphus", "taylor renee"]

# Discord client init
discord = discord.Client()

# Twitch event handling
@twitch.event
async def event_ready():
    """Called once when the bot goes online."""
    print(f"{os.environ['TWITCH_BOT_NICK']} has connected to Twitch!")
    await send_twitch_chat("has arrived!")


@twitch.event
async def event_message(ctx):
    """Runs every time a message is sent in chat."""
    # make sure the bot ignores itself and the streamer
    print(ctx.author.name + ": " + ctx.content)

    update_ctx(ctx)

    if ctx.author.name.lower() in bot_list:
        await raffle_check(ctx.content)
        return

    if is_bot_command(ctx.content):
        await twitch.handle_commands(ctx)


@twitch.command(name='timestamp')
async def handle_timestamp(ctx):
    if ctx.author.is_mod:
        desc = ctx.content.replace('!timestamp ', '')
        await send_timestamp(desc)
        await send_twitch_chat("Successfully sent timestamp to #intl-timestamps!")
    else:
        await send_moderator_permissions_error()


@twitch.command(name='clip')
async def handle_clip(ctx):
    if ctx.author.is_mod:

        clip_url = await twitch.create_clip(os.environ['TWITCH_TMI_TOKEN'],
                                            os.environ['TWITCH_CLIENT_ID'])
        await send_clip(clip_url)
        await send_twitch_chat("@" + ctx.author.name + ", here is your clip of the last 60 seconds: " + clip_url)
    else:
        await send_moderator_permissions_error()


@twitch.command(name='commands')
async def handle_clip():
    await send_twitch_chat("Command list: !timestamp, !clip")


@twitch.command(name='link')
async def handle_link(ctx):
    content = ctx.content.replace('!link ', '')
    url = re.search("(?P<url>https?://[^\s]+)", content).group("url")
    desc = content.replace(url, '')
    message = ctx.author.name + ": " + desc + " - " + url
    await send_twitch_chat(desc + " submitted.")
    await send_link(message)


# Discord event handling
@discord.event
async def on_ready():
    print(f'{discord.user} has connected to Discord!')


@discord.event
async def on_message(message):
    if message.author == discord.user:
        return
    else:
        await relay_message(message)


# Custom Methods

async def send_moderator_permissions_error():
    await send_twitch_chat("Only moderators can use that command!")


async def send_twitch_chat(message):
    msg = "/me " + message
    await twitch._ws.send_privmsg(os.environ['TWITCH_CHANNEL_NAME'], msg)
    # await last_ctx.channel.send(message)


def is_bot_command(message):
    for command in command_list:
        if command in message:
            return True
    return False


def update_ctx(ctx):
    global last_ctx
    if ctx.author.name.lower() in bot_list:
        return
    else:
        last_ctx = ctx


async def raffle_check(message):
    if "a Multi-Raffle has begun for" in message:
        await send_twitch_chat("Oh boy a raffle!")
        await send_twitch_chat("!join")


def check_bot(name):
    if name.lower() in bot_list:
        return True
    else:
        return False


async def relay_message(message):
    if "private" in message.channel.type.name:
        username = message.author.name.lower()
        if username in super_users_list:
            await send_twitch_chat(message.content)
        else:
            return


async def send_timestamp(desc):
    discord_channel = discord.get_channel(int(os.environ['DISCORD_CHANNEL_ID']))
    message = get_UTC_timestamp() + ' - ' + desc
    print("Sending the timestamp message '" + message + "' to Discord")
    await discord_channel.send(message)


async def send_clip(desc):
    channel = discord.get_channel(int(os.environ['DISCORD_CHANNEL_ID']))
    message = get_UTC_timestamp() + ' - ' + desc
    print("Sending the clip message '" + message + "' to Discord")
    await channel.send(message)


async def send_link(message):
    channel = discord.get_channel(768826969252823060)
    await channel.send(message)


def get_UTC_timestamp():
    return datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') + " UTC"


async def start_twitch():
    await twitch.start()


async def start_discord():
    await discord.start(os.environ['DISCORD_TOKEN'])


async def main():
    nest_asyncio.apply()
    twitch_started = start_twitch()
    discord_started = start_discord()
    await asyncio.wait([discord_started, twitch_started])


if __name__ == "__main__":
    loop: asyncio.AbstractEventLoop
    try:
        loop = asyncio.get_event_loop()
        d1, d2 = loop.run_until_complete(main())
    except RuntimeError:
        pass
    finally:
        loop.close()
