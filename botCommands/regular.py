# A LOT OF THE COMMANDS IN THIS FILE ARE SPECIFIC TO THE ECE 2024 SERVER!
# Some of them will be made configurable at a later time :)
#
import os
import pytz
import requests
import urllib.request
from datetime import datetime
from datetime import timedelta

from pytz import timezone
from icalendar import Calendar

import botCommands.checks as checks
from botCommands.utils.utils import *
from botCommands.utils.redisutils import *
from botCommands.utils.ConfigObjects import *

import discord
from discord.ext import commands

WATERLOO_API_KEY = os.getenv("WATERLOO_API_KEY")
THUMBNAIL_LINK = "https://i.imgur.com/Uusxfqa.png"

# Regular
class Regular(commands.Cog, name = 'Regular'):
    def __init__(self, bot):
        self.bot = bot

        # Not really sure what this does
        self._last_member_ = None


    @commands.command()
    async def help(self, ctx):
        embed = discord.Embed(title="Commands", description="Here are a list of commands for the waterloo helper bot",
                              color=0x800080)
        embed.set_footer(text="https://github.com/Kav-K/Stream4Bot")
        embed.set_thumbnail(url=THUMBNAIL_LINK)
        embed.add_field(name="!textbooks", value="Get a link to the textbooks and shared resources", inline=False)
        embed.add_field(name="!upcoming", value="Get a list of upcoming due dates for the next 7 days", inline=False)
        embed.add_field(name="!verify <watid>", value="Verify your account to use this discord", inline=False)
        #embed.add_field(name="!piazza", value="Get our relevant piazza links", inline=False)
        embed.add_field(name="!schedule <OPTIONAL (course number)>", value="View a continuously updating class/lab schedule, or specify a course code for a more specific content/labs/etc schedule.", inline=False)
        embed.add_field(name="!importantdates", value="Get a full calendar with important dates and due dates",
                        inline=False)
        embed.add_field(name="=help", value="Activate the MathBot", inline=False)
        embed.add_field(name="=tex <LATEX>", value="Create a LaTeX equation", inline=False)
        embed.add_field(name="=wolf <QUERY>", value="Use the wolfram engine to search something up or calculate", inline=False)
        embed.add_field(name="!assignments <140 OR 124>", value="View assignment questions for 124 and 140 from the textbook", inline=False)
        embed.add_field(name="!breakdown <course number>", value="View the grading scheme breakdown for a course", inline=False)
        embed.add_field(name="!examinfo", value="Information about ECE exams",
                        inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def textbooks(self, ctx):
        guild = ctx.author.guild
        embed = discord.Embed(title="Textbooks & Resources",
                              description="Here is a dropbox link for our collective resources. Feel free to contact the admin team if you'd like to add to it.",
                              color=0x800080)
        embed.set_footer(text="https://github.com/Kav-K/Stream4Bot")
        embed.set_thumbnail(url=THUMBNAIL_LINK)
        embed.add_field(name="Link", value=getConfigurationValue(ConfigObjects.TEXTBOOKS_LINK,guild),
                        inline=False)
        await ctx.send(embed=embed)


    @checks.channel_check()
    @commands.command()
    async def upcoming(self, ctx, *args):
        dateMap = {}
        dateList = []
        guild = ctx.author.guild

        calendar = None
        try:
            selection = str(args[0])
            if (selection.lower() == "ee"):
                calendar = urllib.request.urlopen(
                    getConfigurationValue(ConfigObjects.IMPORTANT_DATES_LINK_EE, guild))
            elif (selection.lower() == "ce"):
                calendar = urllib.request.urlopen(
                    getConfigurationValue(ConfigObjects.IMPORTANT_DATES_LINK_CE, guild))
            else:
                raise Exception("Default calendar selection")
        except Exception as e:
            calendar = urllib.request.urlopen(
                getConfigurationValue(ConfigObjects.IMPORTANT_DATES_LINK, guild))

        gcal = Calendar.from_ical(calendar.read())
        dateRangeEnd = datetime.now() + timedelta(days=7 if getConfigurationValue(ConfigObjects.UPCOMING_LENGTH,guild) == None else int(getConfigurationValue(ConfigObjects.UPCOMING_LENGTH,guild)))

        # Iterate through components inside of the calendar
        for component in gcal.walk():
            # Checks the event type
            if component.name == "VEVENT":

                # Populates info
                summary = component.get('summary')
                startdate = component.get('dtstart').dt

                # If there is no end date specified
                try:
                    enddate = component.get('dtend').dt
                except:
                    enddate = startdate

                # Initialize timezone
                est = timezone('US/Eastern')

                #Account for if there's no actual time info (e.g all day event?)
                try:
                    finalStartDate = startdate.replace(tzinfo=pytz.utc).astimezone(est)
                    finalEndDate = enddate.replace(tzinfo=pytz.utc).astimezone(est)
                except:
                    finalStartDate = datetime(year=startdate.year, month=startdate.month, day=startdate.day, hour=4,
                                              minute=0).astimezone(est)
                    finalEndDate = datetime(year=enddate.year, month=enddate.month, day=enddate.day, hour=4,
                                            minute=0).astimezone(est)

                # Configures the message with the dates
                if (startdate != enddate):
                    finalMessage = str(
                        finalStartDate.strftime("%A, %B %d at %-I:%M %p")) + " to " + str(
                        finalEndDate.strftime("%A, %B %d at %-I:%M %p") + ";" + summary)
                else:
                    finalMessage = str(
                        finalStartDate.strftime("%A, %B %d at %-I:%M %p")+ ";" + summary)

                # Create a sorted mapping between date and message
                if (datetime.now().date() <= finalStartDate.date() <= dateRangeEnd.date()):
                    if (finalStartDate not in dateMap):
                        dateMap[finalStartDate] = []
                    if (finalStartDate not in dateList):
                        dateList.append(finalStartDate)
                    dateMap[finalStartDate].append(finalMessage)
        dateList.sort()
        embed = discord.Embed(title="Upcoming Important Dates",
                              description="These are all upcoming quizzes, due dates, and other important dates for the upcoming week. Please contact the admin team if there are any issues.",
                              color=0x800080)
        embed.set_footer(text="https://github.com/Kav-K/Stream4Bot")
        embed.set_thumbnail(url=THUMBNAIL_LINK)

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
            if (selection == "252"):
                embed = discord.Embed()
                embed.add_field(name="ECE 252",
                                value="Here is a schedule of topics, tests, quizzes, and assignments for ECE 252",
                                inline=False)
                embed.set_image(url="https://i.imgur.com/xJ6PyvM.png")
                await ctx.send(embed=embed)

            elif (selection == "298"):
                embed = discord.Embed()
                embed.add_field(name="ECE 298",
                                value="Here is a schedule of topics, tests, quizzes, and assignments for ECE 298",
                                inline=False)
                embed.set_image(url="https://i.imgur.com/8wL6e4L.png")
                await ctx.send(embed=embed)

            elif (selection == "224"):

                embed = discord.Embed()

                embed.add_field(name="ECE 224",

                                value="Here is a schedule of topics, tests, quizzes, and assignments for ECE 224",

                                inline=False)
                embed.set_image(url="https://i.imgur.com/W895GA6.png")

                await ctx.send(embed=embed)
            elif (selection == "207"):
                embed = discord.Embed()
                embed.add_field(name="ECE 207",
                                value="Here is a schedule of topics, labs, tests, quizzes, and assignments for ECE 207",
                                inline=False)
                embed.set_image(url="https://i.imgur.com/hIPEvER.png")
                await ctx.send(embed=embed)
            elif (selection == "203"):
                embed = discord.Embed()
                embed.add_field(name="ECE 203",
                                value="Here is a schedule of topics, labs, tests, quizzes, and assignments for ECE 203",
                                inline=False)
                embed.set_image(url="https://i.imgur.com/9vsRdLx.png")
                await ctx.send(embed=embed)
            elif (selection == "208"):
                embed = discord.Embed()
                embed.add_field(name="ECE 208",
                                value="Here is a schedule of topics, labs, tests, quizzes, and assignments for ECE 208",
                                inline=False)
                embed.set_image(url="https://i.imgur.com/Nu6EboE.png")
                await ctx.send(embed=embed)
            elif (selection == "206"):
                embed = discord.Embed()
                embed.add_field(name="ECE 206",
                                value="Here is a schedule of topics, labs, tests, quizzes, and assignments for ECE 206",
                                inline=False)
                embed.set_image(url="https://i.imgur.com/CPKSoKY.png")
                await ctx.send(embed=embed)
            elif (selection == "260"):
                embed = discord.Embed()
                embed.add_field(name="ECE 260",
                                value="Here is a schedule of topics, labs, tests, quizzes, and assignments for ECE 260",
                                inline=False)
                embed.set_image(url="https://i.imgur.com/S2UwB2K.png")
                await ctx.send(embed=embed)
            elif (selection == "231"):
                embed = discord.Embed()
                embed.add_field(name="ECE 231",
                                value="Here is a schedule of topics, labs, tests, quizzes, and assignments for ECE 231",
                                inline=False)
                embed.set_image(url="https://i.imgur.com/LQsnVZN.png")
                await ctx.send(embed=embed)
            else:
                await ctx.send("<@" + str(
                    messageAuthor.id) + "> You must enter a valid course to view a course marking scheme breakdown, valid entries are `252`, `298`, `224`, `207`, `203`, `206`, `260`, `231`, and `208`")

        except:
            embed = discord.Embed(title="Class Schedule",
                                  description="Here is a link to a calendar with class schedules for live lectures and Q&A Sessions. Please contact the admin team if there is anything missing.",
                                  color=0x800080)
            embed.set_footer(text="https://github.com/Kav-K/UWHelperBot")
            embed.set_thumbnail(url=THUMBNAIL_LINK)
            gcal_link_ce = getConfigurationValue(ConfigObjects.SCHEDULE_LINK, messageAuthor.guild)
            ical_link_ce = getConfigurationValue(ConfigObjects.SCHEDULE_LINK_ICAL, messageAuthor.guild)
            gcal_link_ee = getConfigurationValue(ConfigObjects.SCHEDULE_LINK_ALT, messageAuthor.guild)
            ical_link_ee = getConfigurationValue(ConfigObjects.SCHEDULE_LINK_ALT_ICAL, messageAuthor.guild)
            if gcal_link_ce:
                embed.add_field(name="GCal Link (CE)",
                                value=gcal_link_ce,
                                inline=False)
            if ical_link_ce:
                embed.add_field(name="iCal Link (CE)",
                                value=ical_link_ce,
                                inline=False)
            if gcal_link_ee:
                embed.add_field(name="GCal Link (EE)",
                                value=gcal_link_ee,
                                inline=False)
            if ical_link_ee:
                embed.add_field(name="iCal Link (EE)",
                                value=ical_link_ee,
                                inline=False)
            await ctx.send(embed=embed)

    @commands.command()
    async def breakdown(self, ctx, *args):
        messageAuthor = ctx.author
        try:
            selection = args[0]
            if (selection == "203"):
                embed = discord.Embed()
                embed.add_field(name="ECE 203",
                                value="Here is a marking scheme breakdown for ECE 203",
                                inline=False)
                embed.set_image(url="https://i.imgur.com/l49CkwW.png")
                await ctx.send(embed=embed)
            elif (selection == "207"):
                embed = discord.Embed()
                embed.add_field(name="ECE 207",
                                value="Here is a marking scheme breakdown for ECE 207",
                                inline=False)
                embed.set_image(url="https://i.imgur.com/qX3b6Fp.png")
                await ctx.send(embed=embed)
            elif (selection == "224"):
                embed = discord.Embed()
                embed.add_field(name="ECE 224",
                                value="Here is a marking scheme breakdown for ECE 224",
                                inline=False)
                embed.set_image(url="https://i.imgur.com/gtsQboR.png")
                await ctx.send(embed=embed)
            elif (selection == "298"):
                embed = discord.Embed()
                embed.add_field(name="ECE 298",
                                value="Here is a marking scheme breakdown for ECE 298",
                                inline=False)
                embed.set_image(url="https://i.imgur.com/Rgit8J3.png")
                await ctx.send(embed=embed)
            elif (selection == "252"):
                embed = discord.Embed()
                embed.add_field(name="ECE 252",
                                value="Here is a marking scheme breakdown for ECE 252",
                                inline=False)
                embed.set_image(url="https://i.imgur.com/aUjjpQa.png")
                await ctx.send(embed=embed)
            elif (selection == "208"):
                embed = discord.Embed()
                embed.add_field(name="ECE 208",
                                value="Here is a marking scheme breakdown for ECE 208",
                                inline=False)
                embed.set_image(url="https://i.imgur.com/pK7zkYD.png")
                await ctx.send(embed=embed)
            elif (selection == "206"):
                embed = discord.Embed()
                embed.add_field(name="ECE 206",
                                value="Here is a marking scheme breakdown for ECE 206",
                                inline=False)
                embed.set_image(url="https://i.imgur.com/MihMd18.png")
                await ctx.send(embed=embed)
            elif (selection == "260"):
                embed = discord.Embed()
                embed.add_field(name="ECE 260",
                                value="Here is a marking scheme breakdown for ECE 260",
                                inline=False)
                embed.set_image(url="https://i.imgur.com/bHXkemC.png")
                await ctx.send(embed=embed)
            elif (selection == "231"):
                embed = discord.Embed()
                embed.add_field(name="ECE 231",
                                value="Here is a marking scheme breakdown for ECE 231",
                                inline=False)
                embed.set_image(url="https://i.imgur.com/dqqbE6g.png")
                await ctx.send(embed=embed)
            else:

                await ctx.send("<@" + str(
                    messageAuthor.id) + "> You must enter a valid course to view a course marking scheme breakdown, valid entries are `252`, `298`, `224`, `207`, `203`, `206`, `260`, `231`, and `208`")
        except:
            await ctx.send("<@" + str(
                messageAuthor.id) + "> You must enter a course to view a course marking scheme breakdown, valid entries are `252`, `298`, `224`, `207`, `203`, `206`, `260`, `231`, and `208`")

    @checks.channel_check()
    @commands.command()
    async def assignments(self, ctx, *args):
        messageAuthor = ctx.author

        await ctx.send("Currently unavailable")
        return
        #Temp
        try:
            selection = args[0]

            if (selection == "205"):
                embed = discord.Embed()
                embed.add_field(name="ECE 204",
                                value="Here's some assignment information for ECE 205",
                                inline=False)
                embed.set_image(url="https://i.imgur.com/fLgcZXS.png")
                await ctx.send(embed=embed)
            elif (selection == "240"):
                embed = discord.Embed()
                embed.add_field(name="ECE 240",
                                value="Here's some assignment information for ECE 240",
                                inline=False)
                embed.set_image(url="https://i.imgur.com/t4JfgF1.png")
                await ctx.send(embed=embed)
            elif (selection == "204"):
                embed = discord.Embed()
                embed.add_field(name="ECE 204",
                                value="Here's some assignment information for ECE 204",
                                inline=False)

                await ctx.send(embed=embed)
            elif (selection == "109"):
                embed = discord.Embed()
                embed.add_field(name="ECE 109",
                                value="Here's some assignment information for ECE 109",
                                inline=False)
                embed.set_image(url="https://i.imgur.com/soxJspV.png")
                await ctx.send(embed=embed)

            elif (selection == "250"):
                embed = discord.Embed()
                embed.add_field(name="ECE 250",
                                value="Here are some information about ECE 250 labs and quizzes/assignments",
                                inline=False)
                embed.set_image(url="https://i.imgur.com/Wm4VztM.png")
                await ctx.send(embed=embed)
                embed2 = discord.Embed()
                embed2.set_image(url="https://i.imgur.com/pltdo8g.png")
                await ctx.send(embed=embed2)
                embed3 = discord.Embed()
                embed3.set_image(url="https://i.imgur.com/jVVGvXF.png")
                await ctx.send(embed=embed3)
            elif (selection == "222"):
                embed = discord.Embed()
                embed.add_field(name="ECE 222",
                                value="Here's some lab information for ECE 222",
                                inline=False)
                await ctx.send(embed=embed)
            else:
                await ctx.send("<@" + str(
                    messageAuthor.id) + "> you've made an invalid selection! valid entries are `240`, `250`, `204`, `205`, `109`, and `222`")

        except:
            await ctx.send("<@" + str(
                messageAuthor.id) + "> You must enter a course to view assignment sets for, `240`, `250`, `204`, `205`, `109`, and `222`")

    @checks.channel_check()
    @commands.command()
    async def piazza(self, ctx):
        embed = discord.Embed(title="Piazza Links", description="Here are our relevant piazza links.", color=0x800080)
        embed.set_footer(text="https://github.com/Kav-K/UWHelperBot")
        embed.set_thumbnail(url=THUMBNAIL_LINK)
        embed.add_field(name="ECE 205", value="https://piazza.com/class/kjlvbxfnh1f361", inline=False)
        await ctx.send(embed=embed)

    @checks.channel_check()
    @commands.command()
    async def importantdates(self, ctx):
        guild = ctx.author.guild
        embed = discord.Embed(title="Due/Important Dates",
                              description="Here is a link to a calendar with important dates. Please contact the admin team if there is anything missing",
                              color=0x800080)
        embed.set_footer(text="https://github.com/Kav-K/Stream4Bot")
        embed.set_thumbnail(url=THUMBNAIL_LINK)
        embed.add_field(name="Link for CE",
                        value=getConfigurationValue(ConfigObjects.IMPORTANT_DATES_LINK_CE,guild),
                        inline=False)
        embed.add_field(name="Link for EE",
                        value=getConfigurationValue(ConfigObjects.IMPORTANT_DATES_LINK_EE,guild),
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

        embed.set_footer(text="https://github.com/Kav-K/Stream4Bot")
        embed.set_thumbnail(url=THUMBNAIL_LINK)

        await ctx.send(embed=embed)
    @commands.command()
    async def fml(self, ctx):
         #Using this as a reference: https://uwaterloo.ca/registrar/important-dates/entry?id=180
        finalExamDate = datetime.strptime("2021-08-16", "%Y-%m-%d")
        encouragingMessage =  "Hang in there! You've got about " + str((finalExamDate - datetime.now()).days) + " days until this is all over."
        await ctx.send(encouragingMessage)
    @commands.command()
    async def subscribe(self,ctx):
        messageAuthor = ctx.author
        guild = messageAuthor.guild
        if (db_exists(str(messageAuthor.id)+".subscribed",guild) and db_get(str(messageAuthor.id)+".subscribed",guild) == "true"):
            await ctx.send("<@"+str(messageAuthor.id)+"> you are already subscribed for notifications!")
            db_set(str(messageAuthor.id)+".subscribed", "true",guild)
        else:
            db_set(str(messageAuthor.id) + ".subscribed", "true",guild)
            await ctx.send("<@"+str(messageAuthor.id)+"> you have successfully subscribed to notifications!")
            await send_dm(messageAuthor,"You have successfully subscribed to notifications! You will receive important push notifications from the admin team and from upcoming dates here.")

    @commands.command()
    async def unsubscribe(self,ctx):
        messageAuthor = ctx.author
        guild = messageAuthor.guild
        if (db_exists(str(messageAuthor.id)+".subscribed",guild) and db_get(str(messageAuthor.id)+".subscribed",guild) == "true"):
            await ctx.send("<@"+str(messageAuthor.id)+"> you have successfully unsubscribed from all notifications")
            db_set(str(messageAuthor.id)+".subscribed", "false",guild)
        else:
            await ctx.send("<@"+str(messageAuthor.id)+"> you are not currently subscribed to any notifications!")

    @commands.command()
    async def s8(self,ctx):
        s8Role = getRole("Stream 8",ctx.author.guild)
        s1Role = getRole("Section 1", ctx.author.guild)
        s2Role = getRole("Section 2", ctx.author.guild)

        if s1Role not in ctx.author.roles and s2Role not in ctx.author.roles:
            await ctx.author.add_roles(s8Role)
            await ctx.send("<@"+str(ctx.author.id)+"> You have been given the Stream 8 role!")
        else:
            await ctx.send("<@" + str(ctx.author.id) + "> You cannot be granted this role, you are already in Stream 4.")


    @commands.command()
    async def ce(self,ctx):
        ceRole = getRole("CE",ctx.author.guild)
        eeRole = getRole("EE", ctx.author.guild)

        if eeRole not in ctx.author.roles:
            await ctx.author.add_roles(ceRole)
            await ctx.send("<@"+str(ctx.author.id)+"> You have been given the CE role!")
        else:
            await ctx.send("<@"+str(ctx.author.id)+"> You cannot be granted this role, you are already in EE.")

    @commands.command()
    async def ee(self,ctx):
        eeRole = getRole("EE",ctx.author.guild)
        ceRole = getRole("CE", ctx.author.guild)

        if ceRole not in ctx.author.roles:

            await ctx.author.add_roles(eeRole)
            await ctx.send("<@"+str(ctx.author.id)+"> You have been given the EE role!")
        else:
            await ctx.send("<@" + str(ctx.author.id) + "> You cannot be granted this role, you are already in CE.")




    @commands.command()
    async def examinfo(self, ctx):
        embed = discord.Embed(title="Exam Information", color=0x800080)
        embed.set_footer(text="https://github.com/Kav-K/Stream4Bot")
        embed.set_thumbnail(url=THUMBNAIL_LINK)

        embed.add_field(name="EXAM INFO", value="None available currently", inline=False)
        # embed.add_field(name="MATH 119:", value="Begins on Friday, August 7th at 9:00am and submission required by Tuesday, August 11th at 9:00pm", inline=False)
        # embed.add_field(name="ECE 106:", value="Begins Monday, August 10th but can start up until sometime on Tuesday, August 11th. Once started, there will be a limited time. ", inline=False)
        # embed.add_field(name="ECE 124:", value="Begins Tuesday, August 11th at 12:00am and submission required by Wednesday, August 12th at 11:59pm", inline=False)
        # embed.add_field(name="ECE 140:", value="Final Exam (is on/begins) Wednesday, August 12th", inline=False)
        # embed.add_field(name="ECE 108:", value="Begins Wednesday, August 12th at 12:00am and submission is required by Thursday, August 13th at 11:59pm", inline=False)

        await ctx.send(embed=embed)

    @commands.command()
    async def covid(self,ctx):
        URL_COUNTRY_ALL_STATUS = "https://api.covid19api.com/total/country/canada"
        URL_CANADA_TRACKER = "https://api.covid19tracker.ca/summary"

        all_status = requests.get(URL_COUNTRY_ALL_STATUS).json()
        canada_tracker = requests.get(URL_CANADA_TRACKER).json()

        totalConfirmed = all_status[len(all_status) - 1]["Confirmed"]
        totalDead = all_status[len(all_status) - 1]["Deaths"]
        totalRecovered = all_status[len(all_status) - 1]["Recovered"]
        totalActive = all_status[len(all_status) - 1]["Active"]

        

        embed = discord.Embed(title="COVID19 Information Canada", color=0x800080)
        embed.set_footer(text="https://github.com/Kav-K/Stream4Bot")
        embed.set_thumbnail(url=THUMBNAIL_LINK)

        embed.add_field(name="Total Confirmed Cases", value=str(totalConfirmed), inline=False)
        embed.add_field(name="Total Active Cases", value=str(totalActive), inline=False)
        embed.add_field(name="Total Recovered", value=str(totalRecovered), inline=False)
        embed.add_field(name="Total Deaths", value=str(totalDead), inline=False)

        await ctx.send(embed = embed)



