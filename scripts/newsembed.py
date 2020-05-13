"""Script for posting changelog, don't delete as it will come in useful for the future"""

import os
import discord
from discord.ext import commands

client = commands.Bot(command_prefix=",")


@client.event
async def on_ready():
    print("Sending messages..")

    embed = discord.Embed(
        title="Important update!",
        description=":tada: LightsOut has just been updated! Don't worry, if you leave LightsOut as-is nothing will change. Here are some of the major improvments that have been made:",
    )
    embed.add_field(
        name="Customizability",
        value=":question: You can now whilelist what bots are reported on using `,add_bot [@bot]` and `,rem_bot [@bot]`! If you want to view the whitelist, you can do so with `,bots`.",
    )
    embed.add_field(
        name="Troubleshooting",
        value=":crystal_ball: We have added a new `,troubleshoot` command to LightsOut which allows you to get easy infomation if something isn't quite right!",
    )
    embed.add_field(
        name="Polish",
        value=":star2: Over this large update for LightsOut, we have polished, enchanced the experiance of previous functionality and gave an update to our logo :)",
    )
    embed.color = 0xEFEA9A

    for guild in client.guilds:
        for channel in guild.channels:
            if channel.name == "lights-out":
                await channel.send(embed=embed)


client.run(os.environ["TOKEN"])
