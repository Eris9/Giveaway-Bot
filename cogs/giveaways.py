import asyncio
import discord
from discord.errors import HTTPException
from discord.ext import commands, tasks
import datetime
import pytz
import ast
import math
import random
from typing import Optional

class Giveaway(commands.Cog):
	def __init__(self, client):
		self.bot = client
		self.timer.start(client)

	@commands.Cog.listener()
	async def on_reaction_add(self, reaction, user):
		if not str(reaction) == "🎉":
			return
		if user.bot:
			return
		giveaway = await self.bot.db.fetchrow("SELECT giveaway FROM main")
		giveaway = ast.literal_eval(giveaway[0])
		bypassrole = await self.bot.db.fetchrow("SELECT bypass FROM main")
		bypassrole = ast.literal_eval(bypassrole[0])
		for role in bypassrole:
			if role in user.roles:
				giveaway[reaction.message.id]["users"].append(reaction.message.author.id)
				await self.bot.db.execute("UPDATE main SET giveaway = $1", str(giveaway))
				return
		try:
			if giveaway[reaction.message.id]:
				pass
		except:
			return

		if giveaway[reaction.message.id]["bypass"]:
			bypass = reaction.message.guild.get_role(giveaway[reaction.message.id]["bypass"])
			if bypass in user.roles:
				giveaway[reaction.message.id]["users"].append(user.id)
				await self.bot.db.execute("UPDATE main SET giveaway = $1", str(giveaway))
				return

		if giveaway[reaction.message.id]["req"]:
			req = reaction.message.guild.get_role(giveaway[reaction.message.id]["req"])
			if req in user.roles:
				giveaway[reaction.message.id]["users"].append(reaction.message.author.id)
				await self.bot.db.execute("UPDATE main SET giveaway = $1", str(giveaway))
				return
			else:
				embed = discord.Embed(title="Missing Role", description=f"You require the role `{req.name}` for [this](https://discord.com/channels/{reaction.message.guild.id}/{reaction.message.channel.id}/{reaction.message.id}) giveaway.", color=0xff0000)
				await user.send(embed=embed)
				await reaction.message.remove_reaction(str(reaction), user)
				return
		giveaway[reaction.message.id]["users"].append(user.id)
		await savegaw(self, giveaway)

	@commands.Cog.listener()
	async def on_reaction_remove(self, reaction, user):
		if not str(reaction) == "🎉":
			return
		if user.bot:
			return
		giveaway = await self.bot.db.fetchrow("SELECT giveaway FROM main")
		giveaway = ast.literal_eval(giveaway[0])
		try:
			if giveaway[reaction.message.id]:
				pass
		except:
			return
		giveaway[reaction.message.id]["users"].remove(user.id)
		await savegaw(self, giveaway)

	@commands.command()
	async def help(self, ctx):
		embed = discord.Embed(title="Peaky Help Command", description="**?gstart** - Starts the giveaways.\n**?gend** - Ends giveaways.\n**?greroll** - Rerolls winners.", color = 0x00de3b)
		if ctx.message.author.guild_permissions.administrator:
			embed.add_field(name="ADMIN SECTION", value="**?role** - Adds or removes the roles that can use the giveaway commands.", inline=False)
		embed.set_footer(text="Developed by AFinger#0708.")
		await ctx.send(embed=embed)

	@commands.command()
	async def gstart(self, ctx, time: Optional[str], winners: Optional[str], *, reqmsg: Optional[str]):
		perms = await hasperms(self, ctx.author)
		if not perms:
			await ctx.send(f"{ctx.author.mention} you don't have the required permissions to run this command.")
			return
		final = ""
		timetype = ""
		if not time:
			error = await ctx.send(f"{ctx.author.mention} you need enter a valid time.")
			await asyncio.sleep(5)
			await error.delete()
			await ctx.message.delete()
			return
		for i in time:
			if i.isnumeric():
				final += i
			else:
				timetype += i
		if not timetype.lower() == "m" and not timetype.lower() == "s" and not timetype.lower() == "h" and not timetype.lower() == "d":
			error = await ctx.send(f"{ctx.author.mention} you need to include either `s` for seconds, `m` for minutes, `h` for hours or `d` for days.")
			await asyncio.sleep(5)
			await error.delete()
			await ctx.message.delete()
			return
		wordtime = ""
		if timetype.lower() == "s":
			if int(final) < 5:
				error = await ctx.send(f"{ctx.author.mention} you can't make a giveaway less then 5 seconds.")
				await asyncio.sleep(5)
				await error.delete()
				await ctx.message.delete()
				return
			wordtime = f"{final} seconds"
			final = int(final)
		elif timetype.lower() == "m":
			if int(final) == 1:
				wordtime = "1 minute"
			else:
				wordtime = f"{final} minutes"
			final = int(final) * 60
		elif timetype.lower() == "h":
			if int(final) == 1:
				wordtime = "1 hour"
			else:
				wordtime = f"{final} hours"
			final = int(final) * 3600
		elif timetype.lower() == "d":
			if int(final) == 1:
				wordtime = "1 day"
			else:
				wordtime = f"{final} days"
			final = int(final) * 86400
		if not winners:
			error = await ctx.send(f"{ctx.author.mention} you need to include a valid amount of winners")
			await asyncio.sleep(5)
			await error.delete()
			await ctx.message.delete()
			return
		winners = winners.replace("w", "")
		if not winners.isnumeric():
			error = await ctx.send(f"{ctx.author.mention} you need to include a valid amount of winners.")
			await asyncio.sleep(5)
			await error.delete()
			await ctx.message.delete()
			return
		if int(winners) < 1:
			error = await ctx.send(f"{ctx.author.mention} you can't have less than 1 winner.")
			await asyncio.sleep(5)
			await error.delete()
			await ctx.message.delete()
			return
		elif int(winners) > 10:
			error = await ctx.send(f"{ctx.author.mention} you can't have more than 10 winner.")
			await asyncio.sleep(5)
			await error.delete()
			await ctx.message.delete()
			return
		if not reqmsg:
			error = await ctx.send(f"{ctx.author.mention} you need to include a requirement or `None` if there is no requirements then the prize.")
			await asyncio.sleep(5)
			await error.delete()
			await ctx.message.delete()
			return
		req = reqmsg.split()
		reqrole = None
		blackrole = None
		length = 0
		for word in req:
			if "role:" in word.lower():
				role = word.replace("role:", "")
				if not role.isnumeric():
					error = await ctx.send(f"{ctx.author.mention} you have to enter a valid role id.")
					await asyncio.sleep(5)
					await error.delete()
					await ctx.message.delete()
					return
				role = ctx.guild.get_role(int(role))
				if not role:
					error = await ctx.send(f"{ctx.author.mention} you have to enter a valid role id.")
					await asyncio.sleep(5)
					await error.delete()
					await ctx.message.delete()
					return
				reqrole = role
				length += len(word) + 1
			elif "bypass:" in word.lower():
				role = word.replace("bypass:", "")
				if not role.isnumeric():
					error = await ctx.send(f"{ctx.author.mention} you have to enter a valid role id.")
					await asyncio.sleep(5)
					await error.delete()
					await ctx.message.delete()
					return
				role = ctx.guild.get_role(int(role))
				if not role:
					error = await ctx.send(f"{ctx.author.mention} you need to include a valid role id.")
					await asyncio.sleep(5)
					await error.delete()
					await ctx.message.delete()
					return
				blackrole = role
				length += len(word) + 1
			elif "none" in word.lower():
				length += len(word) + 1
		if not length:
			error = await ctx.send(f"{ctx.author.mention} you need to include a requirement or `None` if there is no requirements.")
			await asyncio.sleep(5)
			await error.delete()
			await ctx.message.delete()
			return
		msg = reqmsg[length:]
		if not msg:
			error = await ctx.send(f"{ctx.author.mention} you need to include the prize.")
			await asyncio.sleep(5)
			await error.delete()
			await ctx.message.delete()
			return
		await ctx.message.delete()
		self.timer.cancel()
		giveaway = await self.bot.db.fetchrow("SELECT giveaway FROM main")
		giveaway = ast.literal_eval(giveaway[0])
		tz = pytz.timezone("America/Toronto")
		ct = datetime.datetime.now(tz)
		end = ct + datetime.timedelta(seconds=final)
		enddate = str(end)[:-22].replace("-", "/")
		endtime = ""
		if end.hour > 12:
			if end.minute < 10:
				endtime = f"{end.hour - 12}:0{end.minute}pm"
			else:
				endtime = f"{end.hour - 12}:{end.minute}pm"
		else:
			if end.minute < 10:
				endtime = f"{end.hour}:0{end.minute}am"
			else:
				endtime = f"{end.hour}:{end.minute}am"
		if end.day == ct.day:
			n = f"Today at {endtime}"
		elif end.day - 1 == ct.day:
			n = f"Tomorrow at {endtime}"
		else:
			n = enddate
		if not reqrole and not blackrole:
			embed = discord.Embed(title=msg, description=f"React with :tada: to enter!\nTime: **{wordtime}**\nHosted by: {ctx.author.mention}", color = 0x428bff)
			embed.set_footer(text = f"Winners: {winners} | Ends at: {n}")		
			mesg = await ctx.send("**:tada:GIVEAWAY:tada:**", embed=embed)	
			await mesg.add_reaction("🎉")
			giveaway[mesg.id] = {"title": msg, "host": ctx.author.id, "wordend": endtime, "end": str(end), "winners": winners, "channel": ctx.channel.id, "req": None, "bypass": None, "users": [], "done": False}
		elif reqrole and not blackrole:
			embed = discord.Embed(title=msg, description=f"React with :tada: to enter!\nTime: **{wordtime}**\nHosted by: {ctx.author.mention}\n\n**Requirements:**\nRole: {reqrole.mention}", color = 0x428bff)
			embed.set_footer(text = f"Winners: {winners} | Ends at: {n}")		
			mesg = await ctx.send("**:tada:GIVEAWAY:tada:**", embed=embed)	
			await mesg.add_reaction("🎉")
			giveaway[mesg.id] = {"wordend": wordtime, "title": msg, "host": ctx.author.id, "wordend": endtime, "end": str(end), "winners": winners, "channel": ctx.channel.id, "req": reqrole.id, "bypass": None, "users": [], "done": False}
		elif not reqrole and blackrole:
			embed = discord.Embed(title=msg, description=f"React with :tada: to enter!\nTime: **{wordtime}**\nHosted by: {ctx.author.mention}\n\n**Requirements:**\nBypass Role: {blackrole.mention}", color = 0x428bff)
			embed.set_footer(text = f"Winners: {winners} | Ends at: {n}")		
			mesg = await ctx.send("**:tada:GIVEAWAY:tada:**", embed=embed)	
			await mesg.add_reaction("🎉")
			giveaway[mesg.id] = {"wordend": wordtime, "title": msg, "host": ctx.author.id, "wordend": endtime, "end": str(end), "winners": winners, "channel": ctx.channel.id, "req": None, "bypass": blackrole.id, "users": [], "done": False}
		elif reqrole and blackrole:
			embed = discord.Embed(title=msg, description=f"React with :tada: to enter!\nTime: **{wordtime}**\nHosted by: {ctx.author.mention}\n\n**Requirements:**\nRole: {reqrole.mention}\nBypass Role: {blackrole.mention}", color = 0x428bff)
			embed.set_footer(text = f"Winners: {winners} | Ends at: {n}")		
			mesg = await ctx.send("**:tada:GIVEAWAY:tada:**", embed=embed)	
			await mesg.add_reaction("🎉")
			giveaway[mesg.id] = {"wordend": wordtime, "title": msg, "host": ctx.author.id, "wordend": endtime, "end": str(end), "winners": winners, "channel": ctx.channel.id, "req": reqrole.id, "bypass": blackrole.id, "users": [], "done": False}
		await self.bot.db.execute("UPDATE main SET giveaway = $1", str(giveaway))
		self.timer.start(self.bot)

	@commands.command()
	async def greroll(self, ctx, msgid: Optional[int]):
		perms = await hasperms(self, ctx.author)
		if not perms:
			await ctx.send(f"{ctx.author.mention} you don't have the required permissions to run this command.")
			return
		if not msgid:
			error = await ctx.send(f"{ctx.author.mention} you need to include the message id of the giveaway.")
			await asyncio.sleep(5)
			await error.delete()
			await ctx.message.delete()
			return
		self.timer.cancel()
		giveaway = await self.bot.db.fetchrow("SELECT giveaway FROM main")
		giveaway = ast.literal_eval(giveaway[0])
		for x in giveaway:
			if str(x) == msgid:
				i = giveaway[x]
				channel = self.bot.get_channel(i["channel"])
				title = i["title"]
				winner = random.choice(i["users"])
				winner = await self.bot.fetch_user(winner)
				try:
					embed = discord.Embed(title="You won!", description=f"Congratulations for winning the reroll of [{title}](https://discord.com/channels/{channel.guild.id}/{channel.id}/{x}).\nYou will recieve your payouts soon.", color = 0x00ff00)
					await winner.send(embed=embed)
				except HTTPException:
					await channel.send(f"There was an error sending a message to {winner.mention}.")
				await channel.send(f"Congratulations {winner.mention} for winning the reroll of {title}!\nhttps://discord.com/channels/{channel.guild.id}/{channel.id}/{x}")
				tz = pytz.timezone("America/Toronto")
				i["end"] = str(datetime.datetime.now(tz))
				await savegaw(self, giveaway)
				self.timer.start(self.bot)
				return
		error = await ctx.send(f"{ctx.author.mention} I could not find your giveaway.")
		await asyncio.sleep(5)
		await error.delete()
		await ctx.message.delete()

	@commands.command()
	async def gend(self, ctx, msgid: Optional[str]):
		perms = await hasperms(self, ctx.author)
		if not perms:
			await ctx.send(f"{ctx.author.mention} you don't have the required permissions to run this command.")
			return
		if not msgid:
			error = await ctx.send(f"{ctx.author.mention} you need to include the message id of the giveaway.")
			await asyncio.sleep(5)
			await error.delete()
			await ctx.message.delete()
			return
		self.timer.cancel()
		giveaway = await self.bot.db.fetchrow("SELECT giveaway FROM main")
		temp = ast.literal_eval(giveaway[0])
		giveaway = ast.literal_eval(giveaway[0])
		for x in giveaway:
			if str(x) == msgid:
				i = temp[x]
				channelid = i["channel"]
				channel = self.bot.get_channel(channelid)
				user = await self.bot.fetch_user(i["host"])
				title = i["title"]
				msg = await channel.fetch_message(x)
				winners = i["winners"]
				end = i["wordend"]
				enddate = i["end"][:-22].replace("-", "/")
				winner = None
				winnerlist = []
				if not i["users"]:
					embed = discord.Embed(title="Your giveaway ended.", description=f"Your giveaway for [{title}](https://discord.com/channels/{msg.guild.id}/{channelid}/{x}) has ended.\nThere were no entries", color=000000)
					await user.send(embed=embed)
					await channel.send(f"There were no entries into the {title} giveaway.\nhttps://discord.com/channels/{msg.guild.id}/{channelid}/{x}")
					embed = discord.Embed(title=title, description=f"Winner: None\nHosted by: {user.mention}", color = 0x000000)
					embed.set_footer(text=f"Winners: {winners} | Ends at: {enddate} at {end}")
					await msg.edit(content="**:tada:GIVEAWAY ENDED:tada:**", embed=embed)	
					del temp[x]
				else:
					for f in range(1, int(winners) + 1):
						winner = random.choice(i["users"])
						if not await self.bot.fetch_user(winner) in winnerlist:
							winnerlist.append(await self.bot.fetch_user(winner))
				if winnerlist:
					e = ""
					for w in winnerlist:
						e += f"{w.mention}, "
					e = e[:-2]
					await channel.send(f"Congratulations {e} for winning {title}!\nhttps://discord.com/channels/{msg.guild.id}/{channelid}/{x}")
					for dms in winnerlist:
						try:
							embed = discord.Embed(title="You won!", description=f"Congratulations for winning [{title}](https://discord.com/channels/{msg.guild.id}/{channelid}/{x}).\nYou will recieve your payouts soon.", color = 0x00ff00)
							await dms.send(embed=embed)
						except HTTPException:
							await channel.send(f"There was an error sending a message to {dms.mention}.")
					winnerslist = ""
					if len(winnerlist) > 1:
						winnerslist += "Winners: "
					else:
						winnerslist += "Winner: "
					for users in winnerlist:
						winnerslist += users.mention.join("\n")
						dmwinners = ""
					if len(winnerlist) > 1:
						dmwinners += "Winners: "
					else:
						dmwinners += "The winner is "
					for users in winnerlist:
						dmwinners += f"`{users.name}`, "
					dmwinners = dmwinners[:-2]
					embed = discord.Embed(title="Your giveaway ended.", description=f"Your giveaway for [{title}](https://discord.com/channels/{msg.guild.id}/{channelid}/{x}) has ended.\n{dmwinners}", color=000000)
					await user.send(embed=embed)
					embed = discord.Embed(title=title, description=f"{winnerslist} Hosted by: {user.mention}", color = 0x000000)
					embed.set_footer(text=f"Winners: {winners} | Ends at: {enddate} at {end}")
					await msg.edit(content="**:tada:GIVEAWAY ENDED:tada:**", embed=embed)	
					await msg.reply(content="Please wait patiently for you payouts in <#811087828368490517>.")
					i["done"] = True	
				i["done"] = True
				tz = pytz.timezone("America/Toronto")
				i["end"] = str(datetime.datetime.now(tz))
				await savegaw(self, temp)
				self.timer.start(self.bot)
				return
		await ctx.send(f"{ctx.author.mention} I could not find your giveaway.")
		
	@commands.command()
	async def role(self, ctx, role, arg):
		roles = await self.bot.db.fetchrow("SELECT role FROM main")
		roles = ast.literal_eval(roles[0])
		try:
			role = ctx.guild.get_role(int(role))
		except:
			await ctx.send(f"{ctx.author.mention} I could not find your role.")
			return
		if "add" in arg.lower():
			if not role.id in roles:
				roles.append(role.id)
				await ctx.send(f"{ctx.author.mention} the role {role.name} has successfully been added.")
			else:
				await ctx.send(f"{ctx.author.mention} you have already added this role.")
				return
		elif "remove" in arg.lower():
			if role.id in roles:
				roles.remove(role.id)
				await ctx.send(f"{ctx.author.mention} the role {role.name} has successfully been removed.")
			else:
				await ctx.send(f"{ctx.author.mention} this role has not been added yet.")
				return
		else:
			await ctx.send(f"{ctx.author.mention} you can only add or remove required roles.")
			return
		await self.bot.db.execute("UPDATE main SET role = $1", str(roles))
	
	@commands.command()
	async def bypass(self, ctx, role, arg):
		bypass = []
		await self.bot.db.execute("UPDATE main SET bypass = $1", str(bypass))
		bypass = await self.bot.db.fetchrow("SELECT bypass FROM main")
		bypass = ast.literal_eval(bypass[0])
		try:
			role = ctx.guild.get_role(int(role))
		except:
			await ctx.send(f"{ctx.author.mention} I could not find your role.")
			return
		if "add" in arg.lower():
			if not role.id in bypass:
				bypass.append(role.id)
				await ctx.send(f"{ctx.author.mention} the role {role.name} has successfully been added.")
			else:
				await ctx.send(f"{ctx.author.mention} you have already added this role.")
				return
		elif "remove" in arg.lower():
			if role.id in bypass:
				bypass.remove(role.id)
				await ctx.send(f"{ctx.author.mention} the role {role.name} has successfully been removed.")
			else:
				await ctx.send(f"{ctx.author.mention} this role has not been added yet.")
				return
		else:
			await ctx.send(f"{ctx.author.mention} you can only add or remove required roles.")
			return
		await self.bot.db.execute("UPDATE main SET bypass = $1", str(bypass))

	@tasks.loop(seconds=1)
	async def timer(self, bot):
		await asyncio.sleep(1)
		giveaway = await bot.db.fetchrow("SELECT giveaway FROM main")
		temp = ast.literal_eval(giveaway[0])
		giveaway = ast.literal_eval(giveaway[0])
		if giveaway:
			for x in giveaway:
				i = temp[x]
				if i["done"] == False:
					endtime = datetime.datetime.strptime(i["end"][:-6], "%Y-%m-%d %H:%M:%S.%f")
					tz = pytz.timezone("America/Toronto")
					currenttime = datetime.datetime.strptime(str(datetime.datetime.now(tz))[:-6], "%Y-%m-%d %H:%M:%S.%f")
					timebetween = endtime - currenttime
					seconds = timebetween.total_seconds()
					seconds = round(seconds)
					oseconds = seconds
					if seconds >= 86400:
						days = math.floor(seconds / 86400)
						if days == 1:
							seconds = "1 day"
						else:
							seconds = f"{days} days"
					if str(seconds).isnumeric():
						if seconds >= 3600:
							hours = math.floor(seconds / 3600)
							if hours == 1:
								seconds = "1 hour"
							else:
								seconds = f"{hours} hours"
					if str(seconds).isnumeric():
						if seconds >= 60:
							minutes = math.floor(seconds / 60)
							if minutes == 1:
								seconds = "1 minute"
							else:
								seconds = f"{minutes} minutes"
					if str(seconds).isnumeric():
						if seconds < 60:
							if seconds == 1:
								seconds = "1 second"
							else:
								seconds = f"{seconds} seconds"
					channelid = i["channel"]
					channel = bot.get_channel(channelid)
					user = await bot.fetch_user(i["host"])
					title = i["title"]
					try:
						msg = await channel.fetch_message(x)
					except discord.NotFound:
						del temp[x]
						embed = discord.Embed(title="Deleted Giveaway", description=f"Your giveaway for `{title}` has been deleted.", color=0x000000)
						await user.send(embed=embed)
						await savegaw(self, temp)
						return
					winners = i["winners"]
					end = i["wordend"]
					enddate = i["end"][:-22].replace("-", "/")
					if oseconds < 0:
						winner = None
						winnerlist = []
						if not i["users"]:
							embed = discord.Embed(title="Your giveaway ended.", description=f"Your giveaway for [{title}](https://discord.com/channels/{msg.guild.id}/{channelid}/{x}) has ended.\nThere were no entries", color=000000)
							await user.send(embed=embed)
							await channel.send(f"There were no entries into the {title} giveaway.\nhttps://discord.com/channels/{msg.guild.id}/{channelid}/{x}")
							embed = discord.Embed(title=title, description=f"Winner: None\nHosted by: {user.mention}", color = 0x000000)
							embed.set_footer(text=f"Winners: {winners} | Ends at: {enddate} at {end}")
							await msg.edit(content="**:tada:GIVEAWAY ENDED:tada:**", embed=embed)	
							del temp[x]
						else:
							for f in range(1, int(winners) + 1):
								winner = random.choice(i["users"])
								if not await self.bot.fetch_user(winner) in winnerlist:
									winnerlist.append(await self.bot.fetch_user(winner))
						if winnerlist:
							e = ""
							for w in winnerlist:
								e += f"{w.mention}, "
							e = e[:-2]
							await channel.send(f"Congratulations {e} for winning {title}!\nhttps://discord.com/channels/{msg.guild.id}/{channelid}/{x}")
							for dms in winnerlist:
								try:
									embed = discord.Embed(title="You won!", description=f"Congratulations for winning [{title}](https://discord.com/channels/{msg.guild.id}/{channelid}/{x}).\nYou will recieve your payouts soon.", color = 0x00ff00)
									await dms.send(embed=embed)
								except HTTPException:
									await channel.send(f"There was an error sending a message to {dms.mention}.")
							winnerslist = ""
							if len(winnerlist) > 1:
								winnerslist += "Winners: "
							else:
								winnerslist += "Winner: "
							for users in winnerlist:
								winnerslist += users.mention.join("\n")
							dmwinners = ""
							if len(winnerlist) > 1:
								dmwinners += "Winners: "
							else:
								dmwinners += "The winner is "
							for users in winnerlist:
								dmwinners += f"`{users.name}`, "
							dmwinners = dmwinners[:-2]
							embed = discord.Embed(title="Your giveaway ended.", description=f"Your giveaway for [{title}](https://discord.com/channels/{msg.guild.id}/{channelid}/{x}) has ended.\n{dmwinners}", color=000000)
							await user.send(embed=embed)
							embed = discord.Embed(title=title, description=f"{winnerslist} Hosted by: {user.mention}", color = 0x000000)
							embed.set_footer(text=f"Winners: {winners} | Ends at: {enddate} at {end}")
							await msg.edit(content="**:tada:GIVEAWAY ENDED:tada:**", embed=embed)	
							await msg.reply(content="Please wait patiently for you payouts in <#811087828368490517>.")
							i["done"] = True	
					else:
						if endtime.day == currenttime.day:
							n = f"Today at {end}"
						elif endtime.day - 1 == currenttime.day:
							n = f"Tomorrow at {end}"
						else:
							n = enddate
						if not i["req"] and not i["bypass"]:
							embed = discord.Embed(title=title, description=f"React with :tada: to enter!\nTime: **{seconds}**\nHosted by: {user.mention}", color = 0x428bff)
							embed.set_footer(text=f"Winners: {winners} | Ends at: {n}")
							await msg.edit(embed=embed)	
						elif i["req"] and not i["bypass"]:
							role = msg.guild.get_role(i["req"])
							embed = discord.Embed(title=title, description=f"React with :tada: to enter!\nTime: **{seconds}**\nHosted by: {user.mention}\n\n**Requirements:**\nRole: {role.mention}", color = 0x428bff)
							embed.set_footer(text=f"Winners: {winners} | Ends at: {n}")
							await msg.edit(embed=embed)	
						elif not i["req"] and i["bypass"]:
							role = msg.guild.get_role(i["bypass"])
							embed = discord.Embed(title=title, description=f"React with :tada: to enter!\nTime: **{seconds}**\nHosted by: {user.mention}\n\n**Requirements:**\nBypass Role: {role.mention}", color = 0x428bff)
							embed.set_footer(text=f"Winners: {winners} | Ends at: {n}")
							await msg.edit(embed=embed)	
						elif i["req"] and i["bypass"]:
							bypass = msg.guild.get_role(i["bypass"])
							req = msg.guild.get_role(i["req"])
							embed = discord.Embed(title=title, description=f"React with :tada: to enter!\nTime: **{seconds}**\nHosted by: {user.mention}\n\n**Requirements:**\nRole: {req.mention}\nBypass Role: {bypass.mention}", color = 0x428bff)
							embed.set_footer(text=f"Winners: {winners} | Ends at: {n}")
							await msg.edit(embed=embed)	
				else:
					endtime = datetime.datetime.strptime(i["end"][:-6], "%Y-%m-%d %H:%M:%S.%f")
					tz = pytz.timezone("America/Toronto")
					currenttime = datetime.datetime.strptime(str(datetime.datetime.now(tz))[:-6], "%Y-%m-%d %H:%M:%S.%f")
					time = (currenttime - endtime).total_seconds()
					if time > 604800:
						del temp[x]
			await savegaw(self, temp)

def setup(client):
	client.add_cog(Giveaway(client))

async def hasperms(self, user):
	roles = await self.bot.db.fetchrow("SELECT role FROM main")
	roles = ast.literal_eval(roles[0])
	for role in roles:
		for i in user.roles:
			if role == i.id:
				return True
	return False

async def savegaw(self, dic):
	await self.bot.db.execute("UPDATE main SET giveaway = $1", str(dic))
