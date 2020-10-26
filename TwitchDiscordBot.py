import os
from twitchio.ext import commands
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

# Discord client init
discord = discord.Client()

# Twitch event handling
@twitch.event
async def event_ready():
    """Called once when the bot goes online."""
    print(f"{os.environ['TWITCH_BOT_NICK']} has connected to Twitch!")
    ws = twitch._ws  # this is only needed to send messages within event_ready
    await ws.send_privmsg(os.environ['TWITCH_CHANNEL_NAME'], f"/me has landed!")


@twitch.event
async def event_message(ctx):
    """Runs every time a message is sent in chat."""
    # make sure the bot ignores itself and the streamer
    if ctx.author.name.lower() == os.environ['TWITCH_BOT_NICK'].lower():
        return

    print(ctx.author.name + ": " + ctx.content)
    await twitch.handle_commands(ctx)


@twitch.command(name='timestamp')
async def handle_timestamp(ctx):

    if ctx.author.is_mod:
        desc = ctx.content.replace('!timestamp ', '')
        await send_timestamp(desc)


@twitch.command(name='clip')
async def handle_clip(ctx):
    if ctx.author.is_mod:
        clip_url = await twitch.create_clip(os.environ['TWITCH_TMI_TOKEN'].replace('oauth:', ''), os.environ['TWITCH_CLIENT_ID'])
        await ctx.send("@" + ctx.author.name + ", here is your clip of the last 60 seconds: " + clip_url)
        await send_clip(clip_url)


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


async def send_timestamp(desc):
    channel = discord.get_channel(int(os.environ['DISCORD_CHANNEL_ID']))
    message = get_UTC_timestamp() + ' - ' + desc
    print("Sending the timestamp message '" + message + "' to Discord")
    await channel.send(message)


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
    try:
        loop = asyncio.get_event_loop()
        d1, d2 = loop.run_until_complete(main())
    except Exception as e:
        pass
    finally:
        loop.close()
