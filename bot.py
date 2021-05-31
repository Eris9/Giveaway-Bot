#!/usr/bin/python3
import discord
from discord.ext import commands
import os
import asyncpg

bot = commands.Bot(command_prefix="g?", help_command = None, status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.playing, name= "?help"))

bot.db = bot.loop.run_until_complete(asyncpg.create_pool(database = "gawbot", user = "adam", password = "cW4$7HWk-tw"))

@bot.command()
async def update(ctx):
	if not ctx.author.id == 374147012599218176 and not ctx.author.id == 598164041873227788:
		return
	for filename in os.listdir("./cogs"):
		if filename.endswith(".py"):
			bot.unload_extension(f"cogs.currency.{filename[:-3]}")
	for filename in os.listdir("./cogs"):
		if filename.endswith(".py"):
			bot.load_extension(f"cogs.{filename[:-3]}")
	await ctx.send("Update is live!")

for filename in os.listdir("./cogs"):
		if filename.endswith(".py"):
			bot.load_extension(f"cogs.{filename[:-3]}")

bot.run("")
