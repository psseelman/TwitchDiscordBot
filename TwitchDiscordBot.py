import os
from twitchio.ext import commands
import twitchio
import discord
import asyncio
import nest_asyncio
import datetime
import re
import random

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


@twitch.event
async def event_message(ctx):
    """Runs every time a message is sent in chat."""
    # make sure the bot ignores itself and the streamer
    print(ctx.author.name + ": " + ctx.content)

    await update_ctx(ctx)
    if await check_bot(ctx.author.name.lower()):
        await try_join_raffle(ctx)
        return

    for command in command_list:
        if command in ctx.content:
            await twitch.handle_commands(ctx)


@twitch.command(name='timestamp')
async def handle_timestamp(ctx):
    if ctx.author.is_mod:
        desc = ctx.content.replace('!timestamp ', '')
        await send_timestamp(desc)
        await ctx.send("Successfully sent timestamp to #intl-timestamps!")
    else:
        await send_moderator_permissions_error(ctx)


@twitch.command(name='clip')
async def handle_clip(ctx):
    if ctx.author.is_mod:

        clip_url = await twitch.create_clip(os.environ['TWITCH_TMI_TOKEN'],
                                            os.environ['TWITCH_CLIENT_ID'])
        await send_clip(clip_url)
        await ctx.send("@" + ctx.author.name + ", here is your clip of the last 60 seconds: " + clip_url)
    else:
        await send_moderator_permissions_error(ctx)


@twitch.command(name='commands')
async def handle_clip(ctx):
    await ctx.send("Command list: !timestamp, !clip")


@twitch.command(name='link')
async def handle_link(ctx):
    content = ctx.content.replace('!link ', '')
    url = re.search("(?P<url>https?://[^\s]+)", content).group("url")
    desc = content.replace(url, '')
    message = ctx.author.name + ": " + desc + " - " + url
    await ctx.send(desc + " submitted.")
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

async def send_moderator_permissions_error(ctx):
    await send_twitch_chat(ctx, "Only moderators can use that command!")


async def send_twitch_chat(ctx, message):
    failed = False

    try:
        if ctx is None:
            raise TypeError
        await ctx.send(message)
    except (TypeError, NameError, ValueError, twitchio.errors.EchoMessageWarning):
        failed = True

    if failed:
        global last_ctx
        try:
            await last_ctx.send(message)
        except twitchio.errors.EchoMessageWarning:
            return


async def update_ctx(ctx):
    global last_ctx
    if ctx.author.name.lower() is not "internationalbot":
        last_ctx = ctx


async def try_join_raffle(ctx):
    if "a Multi-Raffle has begun for" in ctx.content:
        await send_twitch_chat(ctx, "Oh boy a raffle!")
        await send_twitch_chat(ctx, "!join")


async def check_bot(name):
    if name.lower() in bot_list:
        return True
    else:
        return False


async def relay_message(message):
    if "private" in message.channel.type.name:
        username = message.author.name.lower()
        if username in super_users_list:
            await send_twitch_chat(None, message.content)
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
    twitch.run()
    return True


async def start_discord():
    discord.run(os.environ['DISCORD_TOKEN'])
    return True


async def main():
    nest_asyncio.apply()
    twitch_started = start_twitch()
    test = await asyncio.sleep(1)
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
