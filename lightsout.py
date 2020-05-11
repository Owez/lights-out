import os
import discord
from discord.ext import commands

client = commands.Bot(command_prefix=",")

client.remove_command("help")

"""Channel name that LightsOut connects to"""
CHANNEL_NAME = "lights-out"


def get_lightsout_channel(guild):
    """Finds the lights-out channel"""

    for channel in guild.channels:
        if channel.name == "lights-out":
            return channel


def join_embed():
    """Generates a join embed"""

    embed = discord.Embed(title="LightsOut Setup")
    embed.add_field(
        name="Important info",
        value="I am all setup, do not remove this channel otherwise I won't be able to report outages!",
    )
    embed.add_field(
        name="Channel permissions",
        value="I will still be able to use this channel if you move it to a hidden section: don't worry, I can still report to this channel. If you ever delete this channel accidently, please add a channel called `#lights-out` and I will be able to report again.",
    )
    embed.add_field(
        name="Getting help",
        value="You can contact my developer or see some further bot infomation by using the `,about` command!",
    )
    embed.color = 0xFFFFFF

    return embed


async def server_setup(guild):
    """Sets a server up"""

    print(
        f"Added to guild '{guild.name}', ID: {guild.id}, Members: {len(guild.members)}"
    )

    await guild.create_text_channel("lights-out")
    channel = get_lightsout_channel(guild)
    await channel.send(embed=join_embed())


@client.event
async def on_ready():
    """Startup"""

    print("LightsOut Bot online!")

    for guild in client.guilds:
        if not get_lightsout_channel(guild):
            await server_setup(guild)


@client.event
async def on_guild_join(guild):
    """Setup channels"""

    await server_setup(guild)


@client.event
async def on_member_update(before, after):
    """Main outage checker"""

    if not after.bot:
        return

    if before.status != after.status:
        got_status = str(after.status)

        if got_status == "online":
            embed = discord.Embed(
                title=f"**{after.name}** is now online!",
                description=f"The bot <@{after.id}> has just became online, you can now use it.",
            )
            embed.color = 0x00FF00

            channel = get_lightsout_channel(after.guild)
            await channel.send(embed=embed)
        elif got_status == "offline":
            embed = discord.Embed(
                title=f"**{after.name}** just disconnected!",
                description=f"The bot <@{after.id}> is no longer online and will not pick up and commands sent!",
            )
            embed.color = 0xFF0000

            channel = get_lightsout_channel(after.guild)
            await channel.send(embed=embed)


@client.command(aliases=["help", "info", "about", "lightsout"],)
async def invite(ctx):
    """Invite infomation"""

    embed = discord.Embed(title="Help/Invite infomation")
    embed.add_field(
        name="Invite link",
        value="https://discord.com/oauth2/authorize?client_id=708817419308761089&permissions=8&scope=bot",
    )
    embed.add_field(
        name="Developer contact",
        value="If you would like to contact my developer, they are <@223903236069785601>!",
    )
    embed.add_field(
        name="Nothing happening?",
        value="You need to allow me have administrator privlages or to be able to send messages to a channel named `#lights-out` or I can't do anything.",
    )
    embed.color = 0xFFFFFF

    await ctx.send(embed=embed)


@client.command(aliases=["servercount"])
async def servers(ctx):
    """Server count"""

    embed = discord.Embed(
        title="Server count",
        description=f"I am currently on {len(client.guilds)} servers!",
    )
    embed.color = 0xFFFFFF

    await ctx.send(embed=embed)


client.run(os.environ["TOKEN"])
