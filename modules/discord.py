from components.logger import Logger

import discord
import re, asyncio, os
from time import time, sleep
from datetime import timedelta
from ast import literal_eval
from fuzzywuzzy import process


class Discord:
    def __init__(self, Database=None, Watcher=None):
        self.dependencies = {"tier":"user", "dependencies":["Database", "Watcher"]}
        self.capabilities = ["ui","input", "output", "blocking", "question"]
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
                #self.logger(guild)
                #get sys channel
                chan = guild.system_channel
                await chan.send(embed=embed)
            self.logger("Startup complete")

        @self.client.event
        async def on_message(message):
            if message.author == self.client.user:
                return
            if self.waitingformsg:
                return 

            # if not using the prefix in a server, disregard
            fromserver = message.guild != None
            if fromserver and message.content[0] != self.prefix:
                return 
            await self.msghandler(message)


    async def msghandler(self, message):
        if message.author == self.client.user:
                return
        
        msg = message.content
        author = str(message.author)
        self.authordict[author] = {"channel": message.channel}
        self.parsemsg(msg, author)
        if "help" in msg:
            ## create embed
            embed = discord.Embed(
                title = "Usage:",
                description = f"Possible commands are:\n{self.commandlist}"
            )
            await message.channel.send(embed=embed)
        else:
            await self.routines.handlecommand(message)

    def parsemsg(self, msg, author):
        arglist = []
        if msg.count(">") > 0:
            for arg in msg.split(">")[1:]: # don't include the first arg
                newarg = arg.lstrip(" ").rstrip(" ")
                arglist.append(newarg)
            self.msgdict[author] = arglist

    def question(self, question):
        preusername = self.db.query(["username", "discord"], "personalia")
        if preusername["succesfull"]:
            username = preusername["resource"]
        else:
            self.logger("Don't know who owns me. exiting.", "alert", "red")
            exit(1)
        channel = self.authordict[username]["channel"]
        self.loop.run_until_complete(message.channel.send(question))
        response, respobj = self.loop.run_until_complete(self.discobj.wait_for_ext("message", check=rescheck, author=username))
        if respobj:
            message = response
            self.logger(response)
        return response

    async def wait_for_ext(self, event, check=None, author=None):
        self.waitingformsg = True
        if author and author in self.msgdict and len(self.msgdict[author]) > 0:
            arglist = self.msgdict[author]
            # save new
            self.msgdict[author] = arglist[1:]
            res = arglist[0]
        else:
            self.waitingformsg = True
            chan = self.authordict[author]["channel"]
            #await chan.send("Yes, I'm listening..")
            res = await self.client.wait_for("message", check=check)
            #res = res.content
            self.waitingformsg = False
            return res.content, res
        self.waitingformsg = False

        return res, None

    def eval(self, t):
        try:
            res = literal_eval(t)
        except:
            res = literal_eval(repr(t))
        return res

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

        # create asyncio loop
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.client = discord.Client()

        bottoken = self.db.query(["discord", "token"], "credentials")["resource"]
        self.loop.create_task(self.client.start(bottoken))
        self.routines = Routines(self.db, self.client, self)
        self.prefix = "!"
        self.commandlist = [x.lower() for x in self.db.membase["ui-interfaces"]["support"]["discord"]]
        self.logger(self.commandlist, "debug")
        self.loop.create_task(self.dostuff())
        self.loop.run_forever()


class Routines:
    def __init__(self, db, client, discobj):
        self.logger = Logger("Discord(routines)").logger
        self.client = client
        self.db = db
        self.discobj = discobj

    async def settings(self, message):
        # create embed
        # implement in databases
        msg = message.content
        author = message.author
        authorname = str(author)
        authusers = ["montarion#0858"]

        if authorname in authusers:
            if message.channel.type is discord.ChannelType.private:
                dmchan = message.channel
            else: # move to dm's
                await message.channel.send("Check your DM's :D")
                if author.dm_channel:
                    dmchan = author.dm_channel
                else:
                    dmchan = await author.create_dm()
            await dmchan.send("Give me a second, I'm gathering everything.")
            self.settingschan = dmchan
        else:
            await message.channel.send(f"Sorry, we're just not that close, {authorname} ..")
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
        await dmchan.send(embed = embed)

        # wait for response
        def rescheck(msg):
            return msg.channel == dmchan and message.author != self.client.user


        while True:
            response = await self.discobj.wait_for_ext("message", check=rescheck, author=authorname)
            category = response
            if category == "exit":
                await dmchan.send("Alright then.. :/")
                return
            if category in self.db.geteditable()["resource"]:
                #self.settingscat = category
                await dmchan.send(f"Selected {category}.")
                await dmchan.send(f"Change data by typing ```[key] = [new data]```.\ne.g. ```city = paris```")
                #self.settingsmode = "datachange"
                break
            else:
                await dmchan.send(f"That is not a valid category. Please pick one of the following:\n {list(self.db.geteditable()['resource'].keys())}")
            await asyncio.sleep(0.1)

        pattern = "(.*) = (.*)"
        while True:
            response = await self.discobj.wait_for_ext("message", check=rescheck, author=authorname)
            msg = response
            if msg == "exit":
                await dmchan.send("Alright then.. :/")
                return

            try:
                x = re.search(pattern, msg)
                key = x.group(1)
                val = x.group(2)
                self.db.write(key, val, category)
                break
            except Exception as e:
                print(e)
                await dmchan.send(f"Sorry, couldn't understand that.\nPlease adhere to the format exactly and try again.")
                return
            asyncio.sleep(0.1)

        await dmchan.send(f"changed data, new value for \"{key}\" is: {val}")

    async def handlecommand(self, message): # filter support earlier
        """allows for command handling"""
        category = message.content.split(" > ")[0]

        # check if from server
        fromserver = message.guild != None
        if fromserver and category[0] == self.discobj.prefix:
            category = category[1:]

        # check if it's an actual command
        if category not in self.discobj.commandlist:
            return
        # grab metadata.json for this command
        metadata = self.db.getmoduledata(category)
        commands = metadata["commands"]
        
        msg = message.content
        author = message.author
        authorname = str(author)

        # start with a main embed
        embed = discord.Embed(
            title = category.capitalize(),
        )
        embed.add_field(
            name="commands",
            value=f"{', '.join(commands)}."
        )
        embed.set_footer(
            text="Please choose a command, or type 'exit'."
        )
        if ">" not in msg:
            await message.channel.send(embed=embed)

        # wait for response
        def rescheck(msg):
            return message.author != self.client.user


        while True:
            response, resobj = await self.discobj.wait_for_ext("message", check=rescheck, author=authorname)

            self.logger(response)
            if response in commands:
                msg = response
                break
            else:
                await message.channel.send(f"That is not a valid option. Valid commands are:\n{commands}")
        curcom = metadata[msg] # current command
        self.logger(curcom["type"], "debug")
        if curcom["type"] == "query":
            #res = self.db.query("lastshow", "anime")["resource"]
            # check for query
            curcom = metadata[msg] # current command
            if curcom["store"] == "db":
                if "table" in curcom:
                    table = curcom["table"]
                else:
                    table = category
                #TODO: fix resource/ status system
                res = self.db.query(curcom["key"], table)["resource"]
            elif curcom["store"] == "query":
                res = self.discobj.watcher.getclass(curcom["classname"])["resource"]
                

            if curcom["return"]["type"] == "embed":
                retdict = curcom["return"]
                titlekey = curcom["return"]["title"]
                self.logger(res, "debug")
                embed = discord.Embed(
                    title=f"{res[titlekey]}"
                )

                if "thumbnail" in retdict:
                    urldict = res
                    self.logger(retdict["thumbnail"], "debug")
                    for k in retdict["thumbnail"]:
                        urldict = urldict[k]
                    url = urldict
                    embed.set_thumbnail(url = url)

                for field in retdict["fields"]:
                    name = field["name"]
                    value = res[field["value"]]
                    if "function" in field:
                        if "class" in field:
                            watcher = self.discobj.watcher
                            self.logger(field["function"], "debug")
                            value = getattr(watcher.getclass(field["class"])["resource"], field["function"])(value)
                        else:
                            if field["function"] in dir(self):
                                value = getattr(self, field["function"])(value)

                    embed.add_field(
                        name=name,
                        value=value
                    )

            await message.channel.send(embed = embed)
            
        elif curcom["type"] == "interactive":
            routinedict = {} # save whatever comes up within this set of routines
            routinedict["channel"] = message.channel
            routines = curcom["routines"]
            for num in sorted(routines):
                routine = routines[num]
                rtype = routine["type"]
                if rtype == "question":
                    # ask question and wait on the reaction
                    name = routine["name"]
                    question = routine["question"]
                    # save result
                    await message.channel.send(question)
                    response, respobj = await self.discobj.wait_for_ext("message", check=rescheck, author=authorname)
                    if respobj:
                        message = respobj
                    routinedict[name] = response
                    
                if rtype == "run": # run function
                    async with message.channel.typing():
                        watcher = self.discobj.watcher
                        prefunc = getattr(watcher.getclass(routine["class"])["resource"], routine["function"])
                        args = [routinedict[x] for x in routine["arguments"]]
                        result = prefunc(*args)["status"]
                        routinedict["status"] = result
                if rtype == "status":
                    if routinedict["status"] == 200:
                        checkmark = "\N{WHITE HEAVY CHECK MARK}"
                        await message.add_reaction(checkmark)
                    else:
                        await message.reply(content="failed..")

        else:
             await message.channel.send(f"That is not a valid option. Not that I know wtf I want..")

    async def compress(self, message):
        msg = message.content
        author = message.author
        authorname = str(author)
        authusers = ["montarion#0858"]


        def eval2(t):
            try:
                res = literal_eval(t)
            except:
                res = literal_eval(repr(t))
            return res

        if authorname not in authusers:
            await message.channel.send(f"Sorry, we're just not that close, {authorname} ..")
            return

        # ask for what should be compressed
        await message.channel.send(f"What would you like to compress?")
        # wait for response
        def rescheck(msg):
            return msg.author != self.client.user


        while True:
            response = await self.discobj.wait_for_ext("message", check=rescheck, author=authorname)
            msg = response

            if msg == "anime":
                # show anime
                embed = discord.Embed(
                    title = "Compression: anime",
                    description = "Please choose a folder, or type it out."
                )

                # this should be inside compression.py..
                storefolder = self.db.query("storelocation", "anime")["resource"]
                basedir = os.getcwd()
                os.chdir(storefolder)
                folderlist = sorted(os.listdir(storefolder), key=os.path.getctime)
                folderlist.reverse()
                # return to base dir
                os.chdir(basedir)

                for i, foldername in enumerate(folderlist):
                    embed.add_field(
                        name=f"{i+1}.",
                        value=foldername
                    )

                await message.channel.send(embed=embed)
                response = await self.discobj.wait_for_ext("message", check=rescheck, author=authorname)
                response = self.discobj.eval(response)
                if type(response) == int:
                    choice = folderlist[response-1]
                else:
                    choice = response
                    pchoice = process.extract(choice, folderlist, limit=5)
                    #cleanup
                    choicelist = []
                    for p in pchoice:
                        choice, ratio = p[0], p[1]
                        #if ratio >= 85:
                        choicelist.append(choice)

                    embed = discord.Embed(
                        title = "Please make a choice",
                    )
                    for i, c in enumerate(choicelist):
                        embed.add_field(
                            name=f"{i+1}.",
                            value=f"{c}"
                        )

                    while True:
                        await message.channel.send(embed=embed)
                        response = await self.discobj.wait_for_ext("message", check=rescheck, author=authorname)
                        response = self.discobj.eval(response)
                        if type(response) == int:
                            choice = choicelist[response-1]
                            break
                        else:
                            await message.channel.send(f"Please pick a number.")

                await message.channel.send(f"You chose {choice}")

                # TODO: send network message to compression capable device
                #       with storagefolder and choice
