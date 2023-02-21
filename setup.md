# Setting up Pollmaster
-this is in a work in progress!!

## Requirements

These steps have been tested on windows 10 with miniconda for Python 3.7 and Docker  
[Miniconda3](https://docs.conda.io/en/latest/miniconda.html)  
[MongoDB](https://www.mongodb.com/try/download/community)

## Installation

-open Anaconda Prompt

Execute the following commands from a terminal window:
```sh
conda create --name pollmaster
conda activate pollmaster
conda install git
(now choose a location at where you want to install pollmaster) Example: cd c:/discordbot/
git clone https://github.com/RJ1002/pollmaster.git
cd pollmaster
conda install pip
pip install -r requirements.txt
```
##  Setup app and bot in Discord 

- Setup an app and a bot using [Creating a Bot Account](https://discordpy.readthedocs.io/en/latest/discord.html#creating-a-bot-account)

## Running the application

- 
- Create a secrets.py in essentials folder in the project. You can use the following template

```python
class Secrets:
    def __init__(self):
        self.dbl_token = ''  # DBL token (only needed for public bot)
        self.mongo_db = 'mongodb://localhost:27017/pollmaster'
        self.bot_token = '' # official discord bot token
        self.mode = 'development' # development or production

SECRETS = Secrets()
```
- After you do the above things:
- open another "Anaconda Prompt" console and enter the following:
```sh
    conda activate pollmaster
    cd [your pollmaster install location] example: cd c:/discordbot/pollmaster
    python ipc.py
```
- now on the console that you used to install pollmaster 
- Run: "python launcher.py"
- You should see the following:
```
[2023-02-20 19:55:12,776 Cluster#Launcher/INFO] Hello, world!
[2023-02-20 19:55:12,777 Cluster#Launcher/INFO] Preparing 1 clusters
[2023-02-20 19:55:12,777 Cluster#Alpha/INFO] Initialized with shard ids [0], total shards 1
[2023-02-20 19:55:12,778 Cluster#Launcher/INFO] Starting Cluster#Alpha
[2023-02-20 19:55:12,788 Cluster#Alpha/INFO] Process started with PID 9272
[2023-02-20 19:55:17,339 Cluster#Alpha/INFO] Process started successfully
[2023-02-20 19:55:17,339 Cluster#Launcher/INFO] Done!
[2023-02-20 19:55:17,340 Cluster#Launcher/INFO] All clusters launched
[2023-02-20 19:55:17,340 Cluster#Launcher/INFO] Startup completed in 4.5637565s
```
##  Invite the bot in Discord 

- Generate url to invite the bot using [Inviting Your Bot](https://discordpy.readthedocs.io/en/latest/discord.html#inviting-your-bot)
- Specify permissions by using the following bit format of the bot permissions appended to the bot invitation url and paste the url in browser and follow the instructions as given in the above url 

> &permissions=1073867840

- Now you will see the bot in your Discord channel
- Try commands like pm!help and pm!new

## Log files

- You can view the log file pollmaster.log in the pollmaster directory
