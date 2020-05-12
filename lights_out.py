import os
import sqlite3
import discord
from discord.ext import commands

"""Channel name that LightsOut connects to"""
CHANNEL_NAME = "lights-out"

"""Path to database (ususally `./lightsout.db`)"""
DB_PATH = "lights_out.db"


client = commands.Bot(command_prefix=",")
client.remove_command("help")

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()


def setup_sqlite_tables() -> str:
    """Gets sql initialsation stuff"""

    with open("init.sql", "r") as file:
        sql_split = file.read().split("\n\n")

        for sql in sql_split:
            c.execute(sql)

    print("Finished database init!")


setup_sqlite_tables()


def get_lightsout_channel(guild: discord.Guild):
    """Finds the lights-out channel"""

    for channel in guild.channels:
        if channel.name == "lights-out":
            return channel


def smart_guild_make(guild: discord.Guild) -> int:
    """Adds guild into db if non existant or returns existing"""

    if not c.execute(f"SELECT {guild.id} FROM guild").fetchone():
        c.execute(f"INSERT INTO guild (id) VALUES ({guild.id})")

        conn.commit()

    return guild.id


def get_guild_bots(guild: discord.Guild) -> list:
    """Pulls all bot ids from db for guild, will return list of int bot ids"""

    query = f"SELECT bot_id FROM guild_bot WHERE guild_id = {guild.id}"

    return [i[0] for i in c.execute(query).fetchall()]


def add_bot_filter(guild: discord.Guild, bot: discord.Member) -> bool:
    """Adds all discord.Member bots in list to db and returns if bot was already in db"""

    in_db = False

    guild_id = smart_guild_make(guild)

    if not c.execute(f"SELECT id from bot where id={bot.id}").fetchone(): # TODO make dedicated function
        c.execute(f"INSERT INTO bot (id) VALUES ({bot.id})")  # Add if not in already

    if c.execute(f"SELECT bot_id from guild_bot where guild_id={guild.id}").fetchone():
        in_db = True
    else:
        c.execute(f"INSERT INTO guild_bot (guild_id, bot_id) VALUES ({guild.id}, {bot.id})")

    conn.commit()

    return in_db


def rem_bot_filter(guild: discord.Guild, bot: discord.Member):
    """Removes bot from whitelist or raises a general [Exception] if it wasn't part of it to begin with"""

    guild_id = smart_guild_make(guild)

    if not c.execute(
        f"SELECT bot_id FROM guild_bot WHERE guild_id={guild.id}"
    ).fetchone():
        raise Exception("Bot isn't in guild's whitelist!")

    pass  # TODO remove


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

    channel = get_lightsout_channel(guild)

    if channel:
        embed = discord.Embed(
            title="Reinvited!",
            description="Please ensure I can still send messages to this channel after any future modifications and that I can also read all member statuses! If you need any help with setup again, you may use `,troubleshoot`",
        )
        embed.color = 0xFFFFFF

        await channel.send(embed=embed)
    else:
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
        title="Command help", description="Useful commands to help you use LightsOut"
    )
    embed.add_field(name=",help", value="Displays what you are reading")
    embed.add_field(
        name=",status",
        value="Shows if LightsOut is setup properly or not on your server, used for diagnosing issues",
        inline=False,
    )
    embed.add_field(
        name=",troubleshoot",
        value="Common issues relating to LightsOut, to be used in combination with `,status`",
        inline=False,
    )
    embed.add_field(
        name=",add_bot [@bot]",
        value="Adds bot to whitelist so only it and other added bots will be reported upon",
        inline=False,
    )
    embed.add_field(
        name=",rem_bot [@bot]", value="Removed bot from whitelist if it was added"
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
    embed.color = 0xFFFFFF

    await ctx.send(embed=embed)


@client.command()
async def status(ctx):
    """Status info regarding LightsOut on ctx.guild"""

    pass  # TODO: simple prompt saying working or not


@client.command(aliases=["rem", "remove", "blacklist"])
async def rem_bot(ctx, user: discord.Member):
    """Removes a bot from the whitelist/filter"""

    if user.bot:
        try:
            rem_bot_filter(ctx.guild, user)

            embed = discord.Embed(
                title="Removed bot from whitelist",
                description=f"<@{user.id}> was removed from the LightsOut whitelist. If you wish to re-add this bot, you may do so using `,add_bot`.",
            )
            embed.color = 0x00FF00
        except:
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


@client.command(aliases=["troubleshooting", "problems", "fix"])
async def troubleshoot(ctx):
    """Troubleshooting tips"""

    embed = discord.Embed(title="Troubleshooting")
    embed.add_field(
        name="Quick diagnostic",
        value="You can run `,status` and I will check that everything is in order!",
        inline=False,
    )
    embed.add_field(
        name="Permissions/roles",
        value="To be able to report outages, I need permissions to read user statuses and send messages to a channel called `#lights-out`. You can re-invite me with admin permissions to simplify this if needed!",
        inline=False,
    )
    embed.add_field(
        name="Status shows its working but nothing is being reported?",
        value="You may have accidently used `,add_bot` on the wrong bot, you can remedy this by using `,rem_bot` (as seen in the `,help` command).",
        inline=False,
    )
    embed.color = 0xFFFFFF

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
    embed.color = 0xFFFFFF

    await ctx.send(embed=embed)


@client.command(aliases=["servercount"])
async def servers(ctx):
    """Server count"""

    embed = discord.Embed(
        title="Server count",
        description=f"I am currently on {len(client.guilds)} servers with {len(list(client.get_all_members()))} members!",
        inline=False,
    )
    embed.color = 0xFFFFFF

    await ctx.send(embed=embed)


client.run(os.environ["TOKEN"])