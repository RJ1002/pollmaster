# Setting up Pollmaster
-work in progress!!

## Requirements

These steps have been tested on windows 10 with miniconda for Python 3.8 
[Miniconda3](https://docs.conda.io/en/latest/miniconda.html)  
[MongoDB](https://www.mongodb.com/try/download/community)

## Installation

-first open "Anaconda Prompt"

Execute the following commands from a terminal window:
```sh
conda create --name pollmaster
conda activate pollmaster
conda install git
conda install python=3.8
(now choose a location at where you want to install pollmaster) Example: cd c:/discordbot/
now get a copy of the code: https://github.com/RJ1002/pollmaster/tree/slash
then extract the zip file of the code and cd to it
conda install pip
pip install -r requirements.txt
```
##  Setup app and bot in Discord 

- Setup an app and a bot using [Creating a Bot Account](https://discordpy.readthedocs.io/en/latest/discord.html#creating-a-bot-account)

## Running the application

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
- now on the console
- Run: python pollmaster.py
- You should see the following(or something similer):
```
Bot running.
```
##  Invite the bot in Discord 

- Generate url to invite the bot using [Inviting Your Bot](https://discordpy.readthedocs.io/en/latest/discord.html#inviting-your-bot)
- Specify permissions by using the following bit format of the bot permissions appended to the bot invitation url and paste the url in browser and follow the instructions as given in the above url 

> &permissions=1073867840
> example invate link: [https://discord.com/oauth2/authorize?client_id=INSERT_CLIENT_ID_HERE&scope=applications.commands%20bot&permissions=1007673537](https://discord.com/oauth2/authorize?client_id=INSERT_CLIENT_ID_HERE&scope=applications.commands%20bot&permissions=1007673537)

- Now you will see the bot in your Discord channel
- Try commands like pm!help and pm!new and /help

## Log files

- You can view the log file pollmaster.log in the pollmaster directory

## bat file info
- for start_pollmaster.bat: the first line you will need to fine your anaconda directory (example: c:/discordbot/miniconda3)
- if you want to set it up to start on windows boot: you can create shortcut of the bat files and put it in your startup folder.
- startup file location: C:\Users\Username\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
