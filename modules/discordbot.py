from components.logger import Logger

import discord
import re
class Discord:
    def __init__(self, Database=None):
        self.dependencies = {"tier":"user", "dependencies":["Database"]}
        self.capabilities = ["ui","input", "output", "blocking"]
        self.db = Database
        #self.timing = {"unit": "minutes", "count":10}
        # do not add init stuff

    def dostuff(self):
        prefix = "!"
        @self.client.event
        async def on_ready():
            self.logger('We have logged in as {0.user}'.format(self.client))
            game = discord.Game("the stonkmarket")
            await self.client.change_presence(status=discord.Status.idle, activity=game)
            ## create embed
            embed = discord.Embed(
                title = "Startup report",
                #description = "Currently no functions are implemented"
            )
            embed.add_field(
                name="Connections",
                value=f"Connected to {len(self.client.guilds)} Servers, and {len(self.client.private_channels)} DMs",
                inline=False
            )
            #send to servers
            for guild in self.client.guilds:
                self.logger(guild)
                #get sys channel
                chan = guild.system_channel
                await chan.send(embed=embed)
            self.logger("Startup complete")

        @self.client.event
        async def on_message(message):
            if message.author == self.client.user:
                return

            if message.content.startswith(prefix):
                msg = message.content
                author = message.author
                if "help" in msg:
                    ## create embed
                    embed = discord.Embed(
                        title = "Usage:",
                        description = "Currently no functions are implemented"
                    )
                    await message.channel.send(embed=embed)
                if "settings" in msg:
                    # create embed
                    # implement in databases
                    authusers = ["montarion#0858"]
                    if author in authusers or True:
                        await message.channel.send("Check your DM's :D")
                        if author.dm_channel:
                            dmchan = author.dm_channel
                        else:
                            dmchan = await author.create_dm()
                        await dmchan.send("Give me a second, I'm gathering everything.")
                        self.settingschan = dmchan
                    else:
                        await message.channel.send(f"Sorry, we're just not that close, {author} ..")
                        return
                    async with dmchan.typing():
                        embed = discord.Embed(
                        title = "Settings mode engaged.",
                        description = "Current user is authorized, settings are accessed."
                        )
                        tables = self.db.geteditable()["resource"]
                        for table in tables:
                            subdict = {}
                            for k in tables[table]:
                                v = tables[table][k]
                                subdict[k] = v
                            res = "\n".join(" = ".join((str(k),str(v))) for k,v in subdict.items())
                            embed.add_field(
                                name=table,
                                value=res,
                                inline=False
                            )

                        embed.add_field(
                            name= "instructions",
                            value="please type the category you want to edit, or type 'exit'"
                        )
                    self.settinguser = author
                    self.settingsmode = "category"
                    #send msg
                    await dmchan.send(embed=embed)
                else:
                    await message.channel.send('Hello!')
            elif not message.guild:
                msg = message.content
                author = message.author

                dmchan = author.dm_channel
                if self.settingsmode == "category" and author == self.settinguser and self.settingschan == message.channel:
                    category = msg
                    if category in self.db.geteditable()["resource"]:
                        self.settingscat = category
                        await dmchan.send(f"Selected {category}.")
                        await dmchan.send(f"Change data by typing ```[key] = [new data]```.\ne.g. ```city = paris```")
                        self.settingsmode = "datachange"
                    else:
                        await dmchan.send(f"That is not a valid category. Please pick one of the following:\n {list(self.db.geteditable()['resource'].keys())}")
                elif self.settingsmode == "datachange" and author == self.settinguser and self.settingschan == message.channel:
                    dmchan = author.dm_channel
                    pattern = "(.*) = (.*)"
                    try:
                        x = re.search(pattern, msg)
                        key = x.group(1)
                        val = x.group(2)
                        self.db.write(key, val, self.settingscat)
                    except Exception as e:
                        print(e)
                        await dmchan.send(f"Sorry, couldn't understand that.\nPlease adhere to the format exactly and try again.")
                        return
                    await dmchan.send(f"changed data, new value for \"{key}\" is: {val}")
                    self.settingsmode = None
                else:
                    dmchan = author.dm_channel
                    await dmchan.send("Sorry, I didn't understand that.")
        self.client.run("NzUwMDQwMDE0NjI4NTg1NDcz.X00vMg.h0WJy7mSEaGl7xWUNc5b9bUD1xQ")

    def query(self, connectionID, query):
        """connectionID is the id of who is asking(starts at 0, database is 999)
           the query is a dict containing the following keys:
            "category", "type", "data", "metadata"
        """
        category = query["category"]
        qtype = query["type"]
        qdata = query.get("data", None)
        metadata = query.get("metadata", None)
        response = {}
        # TODO: Read out the query
        # TODO: Use it to write out the response
        return response


    def startrun(self):
        """Description of what this module does"""
        # init stuff..
        self.logger = Logger("Discord").logger
        self.datapath = f"data/modules/{self.__class__.__name__.lower()}"
        self.client = discord.Client()
        self.dostuff()

