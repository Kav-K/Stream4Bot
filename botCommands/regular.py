import pytz
import requests
import urllib.request
import redis
from datetime import datetime
from datetime import timedelta

from pytz import timezone
from icalendar import Calendar
from botCommands.utils import *
import botCommands.checks as checks

import discord
from discord.ext import commands

banned_channels = ["general","faculty-general","public-discussion","offtopic"]
redisClient = redis.Redis(host='localhost', port=6379, db=0)
WATERLOO_API_KEY = "21573cf6bf679cdfb5eb47b51033daac"

# Regular
class Regular(commands.Cog, name = 'Regular'):
    def __init__(self, bot):
        self.bot = bot

        # Not really sure what this does
        self._last_member_ = None


    @commands.command()
    async def help(self, ctx):
        embed = discord.Embed(title="Commands", description="Here are a list of commands for the stream 4 bot",
                              color=0x800080)
        embed.set_footer(text="An ECE 2024 Stream 4 bot :)")
        embed.set_thumbnail(url="https://api.kaveenk.com/bot/logo.png")
        embed.add_field(name="!textbooks", value="Get a link to the textbooks and shared resources", inline=False)
        embed.add_field(name="!upcoming", value="Get a list of upcoming due dates for the next 7 days", inline=False)
        embed.add_field(name="!verify <watid>", value="Verify your account to use this discord", inline=False)
        embed.add_field(name="!piazza", value="Get our relevant piazza links", inline=False)
        embed.add_field(name="!schedule <OPTIONAL (course number)>", value="View a continuously updating class/lab schedule, or specify a course code for a more specific content/labs/etc schedule.", inline=False)
        embed.add_field(name="!importantdates", value="Get a full calendar with important dates and due dates",
                        inline=False)
        embed.add_field(name="=help", value="Activate the MathBot", inline=False)
        embed.add_field(name="=tex <LATEX>", value="Create a LaTeX equation", inline=False)
        embed.add_field(name="=wolf <QUERY>", value="Use the wolfram engine to search something up or calculate", inline=False)
        embed.add_field(name="!assignments <140 OR 124>", value="View assignment questions for 124 and 140 from the textbook", inline=False)
        embed.add_field(name="!breakdown <course number>", value="View the grading scheme breakdown for a course", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def textbooks(self, ctx):
        embed = discord.Embed(title="Textbooks & Resources",
                              description="Here is a dropbox link for our collective resources. Feel free to contact the admin team if you'd like to add to it.",
                              color=0x800080)
        embed.set_footer(text="An ECE 2024 Stream 4 bot :)")
        embed.set_thumbnail(url="https://api.kaveenk.com/bot/logo.png")
        embed.add_field(name="Link", value="https://www.dropbox.com/sh/tg1se0xab9c9cfc/AAAdJJZXi1bkkHUoW5oYT_EAa?dl=0",
                        inline=False)
        await ctx.send(embed=embed)

    @checks.channel_check()
    @commands.command()
    async def upcoming(self, ctx):
        dateMap = {}
        dateList = []

        # Opens the URL
        calendar = urllib.request.urlopen(
            'https://calendar.google.com/calendar/ical/k5kumara%40edu.uwaterloo.ca/public/basic.ics')
        gcal = Calendar.from_ical(calendar.read())
        dateRangeEnd = datetime.now() + timedelta(days=7)

        # Iterate through components inside of the calendar
        for component in gcal.walk():
            # Checks the event type
            if component.name == "VEVENT":

                # Populates info
                summary = component.get('summary')
                startdate = component.get('dtstart').dt
                enddate = component.get('dtend').dt
                # print(summary)

                # Initialize timezone
                est = timezone('US/Eastern')

                finalStartDate, finalEndDate = None, None
                try:
                    finalStartDate = startdate.replace(tzinfo=pytz.utc).astimezone(est)
                    finalEndDate = enddate.replace(tzinfo=pytz.utc).astimezone(est)
                except:
                    finalStartDate = datetime(year=startdate.year, month=startdate.month, day=startdate.day, hour=4,
                                              minute=0).astimezone(est)
                    finalEndDate = datetime(year=enddate.year, month=enddate.month, day=enddate.day, hour=4,
                                            minute=0).astimezone(est)

                # Configures the message with the dates
                finalMessage = str(
                    finalStartDate.strftime("%A, %B %d at %-I:%M %p")) + " to " + str(
                    finalEndDate.strftime("%A, %B %d at %-I:%M %p") + ";" + summary)

                # Create a sorted mapping between date and message
                if (datetime.now().date() <= finalStartDate.date() <= dateRangeEnd.date()):
                    if (finalStartDate not in dateMap):
                        dateMap[finalStartDate] = []
                    if (finalStartDate not in dateList):
                        dateList.append(finalStartDate)
                    dateMap[finalStartDate].append(finalMessage)
        dateList.sort()
        embed = discord.Embed(title="Upcoming Important Dates",
                              description="These are all upcoming quizzes, due dates, and other important dates. Please contact the admin team if there are any issues.",
                              color=0x800080)
        embed.set_footer(text="An ECE 2024 Stream 4 bot :)")
        embed.set_thumbnail(url="https://api.kaveenk.com/bot/logo.png")

        for idate in dateList:
            for messageToSend in dateMap[idate]:
                messageArray = messageToSend.split(";")
                embed.add_field(name=messageArray[0], value=messageArray[1], inline=False)
        await ctx.send(embed=embed)

        # Closes the page
        calendar.close()

    @checks.channel_check()
    @commands.command()
    async def schedule(self, ctx, *args):
        messageAuthor = ctx.author

        try:
            selection = args[0]
            if (selection == "119"):
                embed = discord.Embed()
                embed.add_field(name="MATH 119",
                                value="Here is a schedule of topics, tests, quizzes, and assignments for MATH 119",
                                inline=False)
                embed.set_image(url="https://api.kaveenk.com/bot/119schedule1.png")
                await ctx.send(embed=embed)
                embed2 = discord.Embed()
                embed2.set_image(url="https://api.kaveenk.com/bot/119schedule2.png")
                await ctx.send(embed=embed2)
            elif (selection == "106"):
                embed = discord.Embed()
                embed.add_field(name="ECE 106",
                                value="Here is a schedule of topics, labs, tests, quizzes, and assignments for ECE 106",
                                inline=False)
                embed.set_image(url="https://api.kaveenk.com/bot/106schedule1.png")
                await ctx.send(embed=embed)
                embed2 = discord.Embed()
                embed2.set_image(url="https://api.kaveenk.com/bot/106schedule2.png")
                await ctx.send(embed=embed2)
                embed3 = discord.Embed()
                embed3.set_image(url="https://api.kaveenk.com/bot/106schedule3.png")
                await ctx.send(embed=embed3)
                embed4 = discord.Embed()
                embed4.add_field(name="Quizzes",
                                value="Quizzes are every monday from 12AM to midnight.",
                                inline=False)
                await ctx.send(embed=embed4)
            elif (selection == "140"):
                embed = discord.Embed()
                embed.add_field(name="ECE 140",
                                value="Here is a schedule of topics, labs, tests, quizzes, and assignments for ECE 140",
                                inline=False)
                embed.set_image(url="https://api.kaveenk.com/bot/140schedule1.png")
                await ctx.send(embed=embed)
            elif (selection == "124"):
                embed = discord.Embed()
                embed.add_field(name="ECE 124",
                                value="Here is a schedule of topics, labs, tests, quizzes, and assignments for ECE 124",
                                inline=False)
                embed.set_image(url="https://api.kaveenk.com/bot/124schedule1.png")
                await ctx.send(embed=embed)
            elif (selection == "108"):
                embed = discord.Embed()
                embed.add_field(name="ECE 108",
                                value="Here is a schedule of topics, labs, tests, quizzes, and assignments for ECE 108",
                                inline=False)
                embed.set_image(url="https://api.kaveenk.com/bot/108schedule1.png")
                await ctx.send(embed=embed)
            elif (selection == "192"):
                embed = discord.Embed()
                embed.add_field(name="ECE 192",
                                value="Here is a schedule of topics, labs, tests, quizzes, and assignments for ECE 192",
                                inline=False)
                embed.set_image(url="https://api.kaveenk.com/bot/192schedule1.png")
                await ctx.send(embed=embed)
            else:
                await ctx.send("<@" + str(
                    messageAuthor.id) + "> You must enter a valid course to view a specific course schedule, valid entries are `140`, `124`, `106`, `119`, `192`, and `108`. Type the command without any options to get a lecture and live session calendar.")

        except:
            embed = discord.Embed(title="Class Schedule",
                                  description="Here is a link to a calendar with class schedules for live lectures and Q&A Sessions. Please contact the admin team if there is anything missing.",
                                  color=0x800080)
            embed.set_footer(text="An ECE 2024 Stream 4 bot :)")
            embed.set_thumbnail(url="https://api.kaveenk.com/bot/logo.png")
            embed.add_field(name="Link",
                            value="https://calendar.google.com/calendar/embed?src=ag2veuvcsc5k4kaqpsv7sp7e04%40group.calendar.google.com&ctz=America%2FToronto",
                            inline=False)
            await ctx.send(embed=embed)

    @commands.command()
    async def breakdown(self, ctx, *args):
        messageAuthor = ctx.author
        try:
            selection = args[0]
            if (selection == "140"):
                embed = discord.Embed()
                embed.add_field(name="ECE 140",
                                value="Here is a marking scheme breakdown for ECE 140",
                                inline=False)
                embed.set_image(url="https://api.kaveenk.com/bot/140breakdown.png")
                await ctx.send(embed=embed)
            elif (selection == "124"):
                embed = discord.Embed()
                embed.add_field(name="ECE 124",
                                value="Here is a marking scheme breakdown for ECE 124",
                                inline=False)
                embed.set_image(url="https://api.kaveenk.com/bot/124breakdown.png")
                await ctx.send(embed=embed)
            elif (selection == "106"):
                embed = discord.Embed()
                embed.add_field(name="ECE 106",
                                value="Here is a marking scheme breakdown for ECE 106",
                                inline=False)
                embed.set_image(url="https://api.kaveenk.com/bot/106breakdown.png")
                await ctx.send(embed=embed)
            elif (selection == "108"):
                embed = discord.Embed()
                embed.add_field(name="ECE 108",
                                value="Here is a marking scheme breakdown for ECE 108",
                                inline=False)
                embed.set_image(url="https://api.kaveenk.com/bot/108breakdown.png")
                await ctx.send(embed=embed)
            elif (selection == "192"):
                embed = discord.Embed()
                embed.add_field(name="ECE 192",
                                value="Here is a marking scheme breakdown for ECE 192",
                                inline=False)
                embed.set_image(url="https://api.kaveenk.com/bot/192breakdown.png")
                await ctx.send(embed=embed)
            elif (selection == "119"):
                embed = discord.Embed()
                embed.add_field(name="MATH 119",
                                value="Here is a marking scheme breakdown for MATH 119",
                                inline=False)
                embed.set_image(url="https://api.kaveenk.com/bot/119breakdown.png")
                await ctx.send(embed=embed)
            else:

                await ctx.send("<@" + str(messageAuthor.id) + "> You must enter a valid course to view a course marking scheme breakdown, valid entries are `140`, `124`, `106`, `119`, `192`, and `108`")
        except:
            await ctx.send("<@" + str(messageAuthor.id) + "> You must enter a course to view a course marking scheme breakdown, valid entries are `140`, `124`, `106`, `119`, `192`, and `108`")

    @checks.channel_check()
    @commands.command()
    async def assignments(self, ctx, *args):
        messageAuthor = ctx.author

        try:
            selection = args[0]

            if (selection == "140"):
                embed = discord.Embed()
                embed.add_field(name="ECE 140",
                                value="Here are the week-based assignment questions for ECE 140",
                                inline=False)
                embed.set_image(url="https://api.kaveenk.com/bot/140assignments.png")
                await ctx.send(embed=embed)
            elif (selection =="124"):
                embed = discord.Embed()
                embed.add_field(name="ECE 124",
                                value="Here are the week-based assignment questions for ECE 124",
                                inline=False)
                embed.set_image(url="https://api.kaveenk.com/bot/124assignments.png")
                await ctx.send(embed=embed)
            else:
                await ctx.send("<@"+str(messageAuthor.id)+"> you've made an invalid selection! The available courses to view assignments for are `140` and `124`")

        except:
            await ctx.send("<@"+str(messageAuthor.id)+"> You must enter a course to view assignment sets for, valid entries are `140` and `124`")

    @commands.command()
    async def piazza(self, ctx):
        embed = discord.Embed(title="Piazza Links", description="Here are our relevant piazza links.", color=0x800080)
        embed.set_footer(text="An ECE 2024 Stream 4 bot :)")
        embed.set_thumbnail(url="https://api.kaveenk.com/bot/logo.png")
        embed.add_field(name="FYE", value="https://piazza.com/class/k9rmr76sakf74o", inline=False)
        embed.add_field(name="ECE 140", value="https://piazza.com/class/k9u2in2foal48e", inline=False)
        embed.add_field(name="MATH 119", value="https://piazza.com/class/k8ykzmozh5241x", inline=False)
        embed.add_field(name="ECE 124", value="https://piazza.com/class/k9eqk9mfo1qy3?cid=1", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def importantdates(self, ctx):
        embed = discord.Embed(title="Due/Important Dates",
                              description="Here is a link to a calendar with important dates. Please contact the admin team if there is anything missing",
                              color=0x800080)
        embed.set_footer(text="An ECE 2024 Stream 4 bot :)")
        embed.set_thumbnail(url="https://api.kaveenk.com/bot/logo.png")
        embed.add_field(name="Link",
                        value="https://calendar.google.com/calendar/embed?src=k5kumara%40edu.uwaterloo.ca&ctz=America%2FToronto",
                        inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def infosessions(self, ctx):
        embed = discord.Embed(title="Co-Op Info Sessions",
                              description="Here is a list of upcoming info sessions",
                              color=0x800080)

        apiResponse = requests.get("https://api.uwaterloo.ca/v2/resources/infosessions.json.?key=" + WATERLOO_API_KEY).json()

        for i, event in enumerate(apiResponse['data']):

            # Only print the 20 upcoming events
            if i > 20:
                break

            # Only prints data if it is after a certain date
            eventDate = datetime.strptime(event['date'], "%Y-%m-%d")

            if eventDate < datetime.now():
                continue

            # Combine information

            dateInformation = eventDate.strftime("%B %d, ") + " at " + event['start_time'] + " to " + event['end_time'] + "\n"

            eventDescription = event['description'][:100] + "...\n"

            eventLink = "[Link to the Event]" + "(" + event['link'] + ") "

            combinedDescription = dateInformation + eventDescription + eventLink

            embed.add_field(name=event['employer'], value = combinedDescription,
                        inline=False)

        embed.set_footer(text="An ECE 2024 Stream 4 bot :)")
        embed.set_thumbnail(url="https://api.kaveenk.com/bot/logo.png")

        await ctx.send(embed=embed)
    @commands.command()
    async def superposition(self, ctx):
        await ctx.send("Superposition is false.")
    @commands.command()
    async def fml(self, ctx):
        # Using this as a reference: https://uwaterloo.ca/registrar/important-dates/entry?id=180
        finalExamDate = datetime.strptime("2020-08-07", "%Y-%m-%d")
        encouragingMessage = "Hang in there! You've got about " + str((finalExamDate - datetime.now()).days) + " days until this is all over."
        await ctx.send(encouragingMessage)
    @commands.command()
    async def subscribe(self,ctx):
        messageAuthor = ctx.author
        if (redisClient.exists(str(messageAuthor.id)+".subscribed") and redisClient.get(str(messageAuthor.id)+".subscribed").decode("utf-8") == "true"):
            await ctx.send("<@"+str(messageAuthor.id)+"> you are already subscribed for notifications!")
            redisClient.set(str(messageAuthor.id)+".subscribed", "true")
        else:
            redisClient.set(str(messageAuthor.id) + ".subscribed", "true")
            await ctx.send("<@"+str(messageAuthor.id)+"> you have successfully subscribed to notifications!")
            await send_dm(messageAuthor,"You have successfully subscribed to notifications! You will receive important push notifications from the admin team and from upcoming dates here.")

    @commands.command()
    async def unsubscribe(self,ctx):
        messageAuthor = ctx.author
        if (redisClient.exists(str(messageAuthor.id)+".subscribed") and redisClient.get(str(messageAuthor.id)+".subscribed").decode("utf-8") == "true"):
            await ctx.send("<@"+str(messageAuthor.id)+"> you have successfully unsubscribed from all notifications")
            redisClient.set(str(messageAuthor.id)+".subscribed", "false")
        else:
            await ctx.send("<@"+str(messageAuthor.id)+"> you are not currently subscribed to any notifications!")



