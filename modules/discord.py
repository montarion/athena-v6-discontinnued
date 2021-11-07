from components.logger import Logger

import discord
import re, asyncio, os, json
from datetime import timedelta
from ast import literal_eval
from fuzzywuzzy import process


class Discord:
    def __init__(self, Database=None, Watcher=None):
        self.dependencies = {"tier":"user", "dependencies":["Database", "Watcher"]}
        #self.capabilities = ["ui","input", "output", "blocking", "question"]
        self.characteristics= ["blocking"]
        self.capabilities = ["discord", "ui", "input", "output", "question"]
        self.db = Database
        self.watcher = Watcher
        #self.timing = {"unit": "minutes", "count":10}
        self.msgdict = {}
        self.authordict = {}
        self.waitingformsg = False
        # do not add init stuff

    async def dostuff(self):
        @self.client.event
        async def on_ready():
            self.logger(f"We have logged in as {self.client.user}")
            game = discord.Game("the stonkmarket")
            await self.client.change_presence(status=discord.Status.online, activity=game)
            ## create embed
            embed = discord.Embed(
                title = "Startup report",
                description = "Type '!help' for help."
            )
            embed.add_field(
                name="Connections",
                value=f"Connected to {len(self.client.guilds)} Servers, and {len(self.client.private_channels)} DMs",
                inline=False
            )
            #send to servers
            for guild in self.client.guilds:
                #get sys channel
                chan = guild.system_channel
                await chan.send(embed=embed)
            self.logger("Startup complete")

        @self.client.event
        async def on_message(message):
            if message.author == self.client.user:
                return
            chan = message.channel
            if message.content.startswith(self.prefix):
                await chan.send("hi there!")

    def startrun(self):
        """Description of what this module does"""
        # init stuff..
        self.logger = Logger("Discord").logger
        self.datapath = f"data/modules/{self.__class__.__name__.lower()}"

        # create asyncio loop
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.client = discord.Client()

        bottoken = self.db.query(["discord", "token"], "credentials")["resource"]
        self.loop.create_task(self.client.start(bottoken))
        #self.routines = Routines(self.db, self.client, self)
        self.prefix = "!"
        self.commandlist = [x.lower() for x in self.db.membase["ui-interfaces"]["support"]["discord"]]
        self.logger(self.commandlist, "debug")
        self.loop.create_task(self.dostuff())
        self.loop.run_forever()


