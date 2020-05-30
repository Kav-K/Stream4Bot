import random
import redis
import requests
import json

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

import discord
from discord.ext import commands

WATERLOO_API_KEY = "21573cf6bf679cdfb5eb47b51033daac"
WATERLOO_API_URL = "https://api.uwaterloo.ca/v2/directory/"

redisClient = redis.Redis(host='localhost', port=6379, db=0)

# Administrative
class Administrative(commands.Cog, name = 'Administrative'):
	def __init__(self, bot):
		self.bot = bot

		# Not really sure what this does
		self._last_member_ = None

	@commands.Cog.listener()
	async def on_ready(self):
		print(f'{self.bot.user.name} has connected to Discord!')

	@commands.Cog.listener()
	async def on_member_join(self, member):
		role = discord.utils.get(member.guild.roles, name="Unverified")
		await member.add_roles(role)

	@commands.command()
	async def verify(self, ctx, *args):
		try:
			messageAuthor = ctx.author
			watid = args[0]

			if (redisClient.exists(str(messageAuthor) + ".request")):
				response = "<@" + str(
					messageAuthor.id) + "> There is already a pending verification request for your WatID," \
										"please use `!confirm <code>` or do `!cancelverification`"
				await ctx.send(response)
				return
			# Ask UW API for information
			apiResponse = requests.get(WATERLOO_API_URL + watid + ".json?key=" + WATERLOO_API_KEY).json()
			email = apiResponse['data']['email_addresses'][0]
			name = apiResponse['data']['full_name']
			user_id = apiResponse['data']['user_id']
			if (apiResponse['data']['department'] != "ENG/Electrical and Computer"):
				response = "<@" + str(
					messageAuthor.id) + "> You are not an ECE student!" \
										"Please manually validate by contacting" \
										"the admin team. The admin team has been" \
										"notified of this incident. <@&706658128409657366>"
				await ctx.send(response)
				return
			if (len(apiResponse['data']['telephone_numbers']) > 0):
				response = "<@" + str(
					messageAuthor.id) + "> You are a faculty member, and faculty members" \
										"require manual validation by an administrative team member." \
										"Please contact the administration team by messaging them directly," \
										"or send an email to k5kumara@uwaterloo.ca."
				await ctx.send(response)
				return;
			if (redisClient.exists(str(messageAuthor) + ".verified")):
				if (int(redisClient.get(str(messageAuthor) + ".verified")) == 1):
					response = "<@" + str(messageAuthor.id) + "> You have already been verified"
					await ctx.send(response)
					return
			if (redisClient.exists(str(user_id))):
				if (int(redisClient.get(str(user_id))) == 1):
					response = "<@" + str(
						messageAuthor.id) + "> This user_id has already been verified. Not you? Contact an admin."
					await ctx.send(response)
					return

			# Mark
			redisClient.set(str(messageAuthor) + ".watid", user_id)
			redisClient.set(str(messageAuthor) + ".verified", 0)
			redisClient.set(str(messageAuthor) + ".name", name)

			# Generate random code
			code = random.randint(1000, 9999)
			redisClient.set(str(messageAuthor), code)

			mailMessage = Mail(
				from_email='verification@kaveenk.com',
				to_emails=email,
				subject='ECE 2024 Section 2 Discord Verification Code',
				html_content='<strong>Your verification code is: ' + str(
					code) + '. Please go back into discord and type !confirm (your code)</strong>')
			try:
				sg = SendGridAPIClient('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')
				mailResponse = sg.send(mailMessage)
				# TODO: Validate mail response
			except Exception as e:
				print(e.message)

			response = "<@" + str(
				messageAuthor.id) + "> I sent a verification code to " + email + ". Find the code" \
									"in your email and type `!confirm <code>` in discord to verify" \
									"your account. Please check your spam and junk folders."
			redisClient.set(str(messageAuthor) + ".request", 1)

			await ctx.send(response)
		except Exception as e:
			print(e)
			response = "<@" + str(
				messageAuthor.id) + "> No WatID provided or invalid watID, please use `!verify <watid>`." \
									"Your WatID is the username in your original email, for example, in " \
									"k5kumara@edu.uwaterloo.ca, the watID is k5kumara."
			await ctx.send(response)

	@commands.command()
	async def confirm(self, ctx, *args):
		try:
			messageAuthor = ctx.author

			code = args[0]

			if (redisClient.exists(str(messageAuthor) + ".request")):

				if (int(code) == int(redisClient.get(str(messageAuthor)))):
					response = "<@" + str(messageAuthor.id) + "> You were successfully verified."

					await ctx.send(response)

					nickname = redisClient.get(str(messageAuthor) + ".name")

					await messageAuthor.edit(nick=str(nickname.decode('utf-8')))

					# Mark user and WatID as verified
					redisClient.set(str(messageAuthor) + ".verified", 1)
					redisClient.set(str(redisClient.get(str(messageAuthor) + ".watid").decode('utf-8')), 1)
					redisClient.delete(str(messageAuthor) + ".request")
					# 706966831268626464
					role = discord.utils.get(ctx.guild.roles, name="Verified")
					unverifiedRole = discord.utils.get(ctx.guild.roles, name="Unverified")
					await messageAuthor.add_roles(role)

					try:
						messageAuthor.remove_roles(unverifiedRole)
					except:
						print("TODO: handle remove_role exception")
				else:
					response = "<@" + str(messageAuthor.id) + "> Invalid verification code."
					await ctx.send(response)
			else:
				response = "<@" + str(
					messageAuthor.id) + "> You do not have a pending verification request, "\
										"please use `!verify <WATID>` to start."
				await ctx.send(response)
		except Exception as e:
			print(e)
			response = "<@" + str(
				messageAuthor.id) + "> There was an error while verifying your user, or your code was invalid."
			await ctx.send(response)

	@commands.command()
	async def cancelverification(self, ctx):

		messageAuthor = ctx.author

		# 706966831268626464
		if (redisClient.exists(str(messageAuthor) + ".request")):
			response = "<@" + str(
				messageAuthor.id) + "> Cancelled your on-going verification, please try again with `!verify <watid>`"
			await ctx.send(response)
		else:
			response = "<@" + str(messageAuthor.id) + "> You do not have a verification in progress"
			await ctx.send(response)

	@commands.command()
	async def devalidate(self, ctx, *args):

		messageAuthor = ctx.author

		allowed = False
		for role in messageAuthor.roles:
			if role.name == 'Admin':
				allowed = True
		if (allowed):
			try:
				selection = args[0]
				if (selection == "user"):
					user = ctx.message.mentions[0]
					watid = redisClient.get(str(user) + ".watid").decode('utf-8')
					redisClient.delete(watid)
					await ctx.send("Unmarked WatID "+watid)
					redisClient.delete(str(user)+".watid")
					await ctx.send("Purged WatID")
					redisClient.delete(str(user) + ".verified")
					await ctx.send("Purged verified status")
					redisClient.delete(str(user) + ".name")
					await ctx.send("Purged legal name")
					redisClient.delete(str(messageAuthor))
					redisClient.delete(str(user)+".request")
					await ctx.send("Purged request status")
					await ctx.send("Purged user from database successfully.")

				elif (selection == "watid"):
					watid = args[1]
					redisClient.delete(watid)
					await ctx.send("Unmarked WatID "+watid)
				else:
					await ctx.send("<@"+str(messageAuthor.id)+"> Invalid selection! You can choose to devalidate a user or a WatID.")
			except:
				print("<@+"+str(messageAuthor.id)+"> Invalid syntax or selection: `!devalidate <select 'user' or 'watid'> <value>`")

	@commands.command()
	async def correlate(self, ctx, *args):

		messageAuthor = ctx.author

		allowed = False
		for role in messageAuthor.roles:
			if role.name == 'Admin':
				allowed = True
		if (allowed):
			try:
				user = ctx.message.mentions[0]
				watid = args[1]

				try:
					ranks = args[2]
				except:
					await ctx.send("No ranks supplied, not applying any ranks.")
					ranks = ""

				try:
					apiResponse = requests.get(WATERLOO_API_URL + watid + ".json?key=" + WATERLOO_API_KEY).json()
					name = apiResponse['data']['full_name']
				except:
					await ctx.send("Invalid WatID: "+watid)
					return

				redisClient.set(str(user) + ".watid", watid)
				await ctx.send("WatID "+watid+" has been validated and correlated to <@"+str(user.id)+">")
				if ("Verified" in ranks):
					redisClient.set(str(user) + ".verified", 1)
					await ctx.send("<@" + str(user.id) + "> has been set to Verified status")
				redisClient.set(str(user) + ".name", name)
				await user.edit(nick=name)
				await ctx.send(
					"Name " + name + " has been validated and correlated to <@" + str(user.id) + ">")
				redisClient.set(str(redisClient.get(str(messageAuthor) + ".watid").decode('utf-8')), 1)
				await ctx.send(
					"The WatID " + watid + " has been marked for no further verifications.")


				#Set ranks
				isTeaching = False
				for role in user.roles:
					if role.name == 'Teaching Staff' or role.name == "Professor" or role.name == "Teaching Assistant":
						isTeaching = True
				if (isTeaching):
					if ("Verified" in ranks or "Guest" in ranks):
						await ctx.send("<@"+str(messageAuthor.id)+"> You may not apply your selected roles to this person.")
						return
				try:
					rank_array = ranks.split(",")
					for rank in rank_array:
						if (rank == ""): break
						if ("_" in rank):
							rank = rank.replace("_"," ")
						rankToGive = discord.utils.get(ctx.message.guild.roles, name=rank.strip())

						await user.add_roles(rankToGive)

						await ctx.send("Added " + rank + " role to <@" + str(user.id) + ">")

				except Exception as e:

					await user.add_roles(discord.utils.get(ctx.message.guild.roles,name=ranks.strip()))



				await ctx.send("All tasks completed successfully")
			except Exception as e:
				print(str(e))
				print('t4')
				await ctx.send("<@"+str(messageAuthor.id)+"> You have entered invalid syntax, or the user you are trying to correlate is invalid. `!correlate <USER MENTION> <WatID>`")
	
	@commands.command()
	async def ldaplookup(self, ctx, *args):

		messageAuthor = ctx.author

		allowed = False
		for role in messageAuthor.roles:
			if role.name == 'Admin' or role.name == 'Professor':
				allowed = True

		if (allowed):
			try:

				watid = args[0]

				if ("@" in args[0]):

					# Find user's discord tag
					for member in ctx.message.mentions:
						discordID = str(member)
						watid = redisClient.get(discordID + ".watid").decode('utf-8')
						break
				apiResponse = requests.get(WATERLOO_API_URL + watid + ".json?key=" + WATERLOO_API_KEY).json()

				embed = discord.Embed(title="LDAP Lookup",
									  description="Here is an internal lookup by the University of Waterloo",
									  color=0x800080)
				embed.set_footer(text="An ECE 2024 Stream 4 bot :)")
				embed.set_thumbnail(url="https://i.imgur.com/UWyVzwu.png")
				embed.add_field(name="Status",
								value=apiResponse['meta']['message'],
								inline=False)
				embed.add_field(name="Full Name",
								value=apiResponse['data'][
									'full_name'],
								inline=False)
				embed.add_field(name="Department",
								value=apiResponse['data']['department'],
								inline=False)
				embed.add_field(name="Common Names",
								value=str(
									apiResponse['data']['common_names']),
								inline=False)
				embed.add_field(name="Emails",
								value=str(
									apiResponse['data']['email_addresses']),
								inline=False)
				embed.add_field(name="Offices",
								value=str(
									apiResponse['data']['offices']),
								inline=False)
				embed.add_field(name="Phone Numbers",
								value=str(
									apiResponse['data']['telephone_numbers']),
								inline=False)

				if (apiResponse['data']['department'] == "ENG/Electrical and Computer"):
					embed.add_field(name="Student Status",
									value="ECE Student",
									inline=False)
				else:
					embed.add_field(name="Student Status",
									value="Not an ECE Student",
									inline=False)
				if (len(apiResponse['data']['telephone_numbers']) > 0):
					embed.add_field(name="Student Status",
									value="NOT A STUDENT. MANUAL VALIDATION REQUIRED",
									inline=False)
				await ctx.send(embed=embed)
			except Exception as e:
				response = "Invalid WatID or no WatID provided"
				print(str(e))
				await ctx.send(response)
		else:
			response = "You are not allowed to use this command. Local Directory Access Protocol Lookups are restricted to Administrators"
			await ctx.send(response)

	@commands.command()
	async def validateroles(self, ctx):

		messageAuthor = ctx.author

		allowed = False
		for role in messageAuthor.roles:
			if role.name == 'Admin':
				allowed = True
		if (allowed):
			verifiedRole = discord.utils.get(ctx.message.guild.roles, name="Verified")
			unverifiedRole = discord.utils.get(ctx.message.guild.roles, name="Unverified")
			adminRole = discord.utils.get(ctx.message.guild.roles, name="Admin")
			teachingRole = discord.utils.get(ctx.message.guild.roles, name="Teaching Staff")

			memberList = ctx.message.guild.members
			for member in memberList:
				if (verifiedRole in member.roles and unverifiedRole in member.roles):
					await ctx.send("Removed unverified role from " + member.name)
					await member.remove_roles(unverifiedRole)
				elif (
						verifiedRole not in member.roles and unverifiedRole not in member.roles and adminRole not in member.roles and teachingRole not in member.roles):
					await ctx.send("Added unverified role to " + member.name)
					await member.add_roles(unverifiedRole)
			await ctx.send("All role validations completed successfully.")
