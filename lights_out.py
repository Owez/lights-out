import os
import sqlite3
import datetime
import discord
from discord.ext import commands

"""Channel name that LightsOut connects to"""
CHANNEL_NAME = "lights-out"

"""Path to database (ususally `./lightsout.db`)"""
DB_PATH = "lights_out.db"

"""ID of channel to send reports to"""
REPORT_CHANNEL_ID = 709893017196167238


client = commands.Bot(command_prefix=",")
client.remove_command("help")

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()


def setup_sqlite_tables() -> str:
    """Gets sql initialsation stuff"""

    with open("scripts/init.sql", "r") as file:
        sql_split = file.read().split("\n\n")

        for sql in sql_split:
            c.execute(sql)

    print("Finished database init!")


setup_sqlite_tables()


def get_lightsout_channel(guild: discord.Guild):
    """Finds the lights-out channel"""

    for channel in guild.channels:
        if channel.name == CHANNEL_NAME:
            return channel


def smart_make_guild(guild: discord.Guild) -> int:
    """Adds guild into db if non existant or returns existing"""

    if not c.execute(f"SELECT {guild.id} FROM guild").fetchone():
        c.execute(f"INSERT INTO guild (id) VALUES ({guild.id})")

        conn.commit()

    return guild.id


def smart_make_bot(bot: discord.Member) -> int:
    """Similar to [smart_make_guild], adds a bot to db"""

    if not c.execute(f"SELECT id from bot where id={bot.id}").fetchone():
        c.execute(f"INSERT INTO bot (id) VALUES ({bot.id})")

        conn.commit()

    return bot.id


def get_guild_bots(guild: discord.Guild) -> list:
    """Pulls all bot ids from db for guild, will return list of int bot ids"""

    query = f"SELECT bot_id FROM guild_bot WHERE guild_id = {guild.id}"

    return [i[0] for i in c.execute(query).fetchall()]


def add_bot_filter(guild: discord.Guild, bot: discord.Member) -> bool:
    """Adds all discord.Member bots in list to db and returns if bot was already in db"""

    in_db = False

    smart_make_guild(guild)  # ensure guild is there
    smart_make_bot(bot)  # ensure bot is there

    if bot.id in get_guild_bots(guild):
        in_db = True
    else:
        c.execute(
            f"INSERT INTO guild_bot (guild_id, bot_id) VALUES ({guild.id}, {bot.id})"
        )

    conn.commit()

    return in_db


def rem_bot_filter(guild: discord.Guild, bot: discord.Member):
    """Removes bot from whitelist or raises a general [Exception] if it wasn't
    part of it to begin with and returns if user was never in whitelist"""

    guild_id = smart_make_guild(guild)

    if bot.id not in get_guild_bots(guild):
        return False

    c.execute(f"DELETE FROM guild_bot WHERE bot_id={bot.id} AND guild_id={guild.id}")
    conn.commit()

    return True


def join_embed():
    """Generates a join embed"""

    embed = discord.Embed(title="LightsOut Setup")
    embed.add_field(
        name="Important info",
        value="I am all setup, do not remove this channel otherwise I won't be able to report outages!",
        inline=False,
    )
    embed.add_field(
        name="Customizing",
        value="If you would like me to only report outages for specific bots, please run `,bots @bot @other_bot` for all the bots you would like me to report on!",
        inline=False,
    )
    embed.add_field(
        name="Channel permissions",
        value="If you move it to a hidden section I can still report to this channel **if I have admin permissions**. If you ever delete this channel accidently, please add a channel called `#lights-out` and I will be able to report again.",
        inline=False,
    )
    embed.add_field(
        name="Getting help",
        value="To see avalible commands, you may run `,help` or if you would like to contact my developer or see some further bot infomation, you can do so by using the `,about` command!",
        inline=False,
    )
    embed.color = 0xEFEA9A

    return embed


async def server_setup(guild):
    """Sets a server up"""

    smart_make_guild(
        guild
    )  # faster for future quick updates, always ran once for each server

    try:
        await guild.create_text_channel("lights-out")
        channel = get_lightsout_channel(guild)
        await channel.send(embed=join_embed())
        print(
            f"Added to guild '{guild.name}', ID: {guild.id}, Members: {len(guild.members)}"
        )
    except:
        print(
            f"Missing permissions for guild '{guild.name}', ID: {guild.id}, Members: {len(guild.members)}"
        )


@client.event
async def on_ready():
    """Startup"""

    print("LightsOut Bot online!")

    await client.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(client.guilds)} servers. Do ,help",
        )
    )

    for guild in client.guilds:
        if not get_lightsout_channel(guild):
            await server_setup(guild)


@client.event
async def on_guild_join(guild):
    """Setup channels"""

    channel = get_lightsout_channel(guild)

    if channel:
        embed = discord.Embed(
            title="Reinvited!",
            description="Please ensure I can still send messages to this channel after any future modifications and that I can also read all member statuses! If you need any help with setup again, you may use `,troubleshoot`",
        )
        embed.color = 0xEFEA9A

        await channel.send(embed=embed)
    else:
        await server_setup(guild)


@client.event
async def on_member_update(before, after):
    """Main outage checker"""

    if not after.bot or after.id not in get_guild_bots(after.guild):
        return

    if before.status != after.status:
        got_status = str(after.status)

        if got_status == "online":
            embed = discord.Embed(
                title=f"**{after.name}** is now online!",
                description=f"The bot <@{after.id}> has just became online, you can now use it.",
                inline=False,
            )
            embed.color = 0x00FF00

            channel = get_lightsout_channel(after.guild)
            await channel.send(embed=embed)
        elif got_status == "offline":
            embed = discord.Embed(
                title=f"**{after.name}** just disconnected!",
                description=f"The bot <@{after.id}> is no longer online and will not pick up and commands sent!",
                inline=False,
            )
            embed.color = 0xFF0000

            channel = get_lightsout_channel(after.guild)
            await channel.send(embed=embed)


@client.command()
async def help(ctx):
    """Help infomation regarding commands"""

    embed = discord.Embed(
        title="Command help",
        description="Useful commands to help you use LightsOut",
        inline=False,
    )
    embed.add_field(
        name=",bots",
        value="Shows whitelist/what bots are allowed (if no whitelist if active, all bots are allowed)",
        inline=False,
    )
    embed.add_field(
        name=",add_bot [@bot]",
        value="Adds bot to whitelist so only it and other added bots will be reported upon",
        inline=False,
    )
    embed.add_field(
        name=",rem_bot [@bot]",
        value="Removed bot from whitelist if it was added",
        inline=False,
    )
    embed.add_field(
        name=",about",
        value="Invite and contact infomation along with a prompt of where to find troubleshooting info",
        inline=False,
    )
    embed.add_field(
        name=",servers",
        value="Shows statistics on what servers LightsOut is in",
        inline=False,
    )
    embed.add_field(
        name=",troubleshoot",
        value="Common issues relating to LightsOut and how to fix them",
        inline=False,
    )
    embed.add_field(
        name=",report [info]",
        value="Reports an issue directly to my developer",
        inline=False,
    )
    embed.add_field(name=",help", value="Displays what you are reading", inline=False)
    embed.color = 0xEFEA9A

    await ctx.send(embed=embed)


@client.command(aliases=["rem", "remove", "blacklist"])
async def rem_bot(ctx, user: discord.Member):
    """Removes a bot from the whitelist/filter"""

    if user.bot:
        if rem_bot_filter(ctx.guild, user):
            embed = discord.Embed(
                title="Removed bot from whitelist",
                description=f"<@{user.id}> was removed from the LightsOut whitelist. If you wish to re-add this bot, you may do so using `,add_bot`.",
            )
            embed.color = 0x00FF00
        else:
            embed = discord.Embed(
                title="Bot not in whitelist!",
                description="This bot is not a part of the whitelist and therefore cannot be removed from it! If you are having problems, you may find `,troubleshoot` useful!",
            )
            embed.color = 0xFF0000
    else:
        embed = discord.Embed(
            title="Given user is not a bot!",
            description=f"<@{user.id}> is not a bot and cannot be removed from the whitelist!",
        )
        embed.color = 0xFF0000

    await ctx.send(embed=embed)


@client.command(aliases=["bot", "whitelist", "add"])
async def add_bot(ctx, user: discord.Member):
    """Filters for specific bots"""

    if user.bot:
        if add_bot_filter(ctx.guild, user):
            embed = discord.Embed(
                title="Bot already in whitelist",
                description=f"<@{user.id}> is already in the whitelist, no need to change anything!",
            )
            embed.color = 0x00FF00
        else:
            embed = discord.Embed(
                title="Added bot to whitelist",
                description=f"<@{user.id}> has been added to the whitelist. Only whitelisted bots will be reported in `#lights-out`.",
            )
            embed.add_field(
                name="Removing bots",
                value="You can remove bots using the `,remove_bot` command. If no bots are whitelisted, all bots are reported!",
                inline=False,
            )
            embed.color = 0x00FF00
    else:
        embed = discord.Embed(
            title="Given user is not a bot!",
            description=f"<@{user.id}> is not a bot and cannot be added to the LightsOut filter!",
        )
        embed.color = 0xFF0000

    await ctx.send(embed=embed)


@client.command(aliases=["listbot", "botlist"])
async def bots(ctx):
    """Lists bots active on this server"""

    whitelisted = get_guild_bots(ctx.guild)

    if len(whitelisted) == 0:
        embed = discord.Embed(
            title="Whitelisted bots",
            description="There is no whitelist in place and all bots are reported upon! You may add a bot to the whitelist with `,add_bot`.",
        )
    else:
        embed = discord.Embed(
            title="Whitelisted bots",
            description="Below is a list of bots that are reported in `#lights-out`. If you would like to remove one, you can do do with the `,rem_bot` command.",
        )

        for ind, bot in enumerate(whitelisted):
            embed.add_field(
                name=f"Whitelisted bot #{ind + 1}",
                value=f"<@{bot}> is whitelisted and together with other whitelisted bots will be the only ones reported",
                inline=False,
            )

    embed.color = 0xEFEA9A

    await ctx.send(embed=embed)


@client.command(aliases=["problem"])
async def report(ctx, *, info: str):
    """Reports problem"""

    sent_embed = discord.Embed(
        title="Sending report",
        description="Thank you for reporting this issue, here is a preview of the report sent to the developer (see `,about`):",
    )
    sent_embed.color = 0xEFEA9A

    await ctx.send(embed=sent_embed)

    report_embed = discord.Embed(title="New report")
    report_embed.add_field(name="Info", value=info, inline=False)
    report_embed.add_field(
        name="Sent by",
        value=f"This report was sent by <@{ctx.author.id}>",
        inline=False,
    )
    report_embed.add_field(
        name="Submitted date",
        value=f"This report was submitted at {datetime.datetime.utcnow()}",
    )
    report_embed.color = 0x000000

    channel = client.get_channel(REPORT_CHANNEL_ID)

    await ctx.send(embed=report_embed)
    await channel.send(embed=report_embed)


@client.command(aliases=["troubleshooting", "fix", "status"])
async def troubleshoot(ctx):
    """Troubleshooting tips"""

    embed = discord.Embed(
        title="Troubleshooting",
        description="Some common issues faced when first setting up LightsOut and how to fix them",
    )
    embed.add_field(
        name="Permissions/roles",
        value="To be able to report outages, I need permissions to read user statuses and send messages to a channel called `#lights-out`. You can re-invite me with admin permissions to simplify this if needed!",
        inline=False,
    )
    embed.add_field(
        name="Status shows its working but nothing is being reported?",
        value="You may have accidently used `,add_bot` on the wrong bot, you can remedy this by using `,rem_bot`.",
        inline=False,
    )
    embed.add_field(
        name="Think it's a bug?",
        value="You can report bugs directly to my developer with the `,report` command!",
        inline=False,
    )
    embed.color = 0xEFEA9A

    await ctx.send(embed=embed)


@client.command(aliases=["info", "lightsout"],)
async def about(ctx):
    """Bot about info"""

    embed = discord.Embed(title="About/Invite infomation")
    embed.add_field(
        name="Invite link",
        value="https://discord.com/oauth2/authorize?client_id=708817419308761089&permissions=8&scope=bot",
        inline=False,
    )
    embed.add_field(
        name="Developer contact",
        value="If you would like to contact my developer, they are <@223903236069785601>!",
        inline=False,
    )
    embed.add_field(
        name="Nothing happening?",
        value="You can view troubleshooting infomation with `,troubleshoot` or find a list of commands with `,help`.",
        inline=False,
    )
    embed.color = 0xEFEA9A

    await ctx.send(embed=embed)


@client.command(aliases=["servercount"])
async def servers(ctx):
    """Server count"""

    embed = discord.Embed(
        title="Server count",
        description=f"I am currently on {len(client.guilds)} servers with {len(list(client.get_all_members()))} members!",
        inline=False,
    )
    embed.color = 0xEFEA9A

    await ctx.send(embed=embed)


client.run(os.environ["TOKEN"])
