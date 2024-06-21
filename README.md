# eZwizard3-bot
A discord bot that connects to your jb ps4 (9.00 only atm) to allow other people to do save things with it

this project is activily being worked on by Zhaxxy and is very passionate about it, please feel free to ask for any suggestions, reporting any bugs, or even making your own changes and make a pull request, ill be sure to respond!

# Known issues
~~If theres more then one connection to the ps4 at a time it is very likley that the bot will fail and get `RuntimeError: coroutine ignored GeneratorExit` so make sure theres nothing else connected to the ps4 network. That error also ignores any context managers so if it happens the bot will likley be stuck and ps4 need reboot, PLEASE ANYONE TELL ME HOW TO FIX THIS

bot can sometimes get stuck at some part which involves the mounted_saves_at_once semaphore, which will cause it to get stuck on other commands, which will start spamming chats with tick tocks eventually, my suspicon is that it has something to do with the discord api libary interactions.py which im using~~
I seem to have fixed it using mutiple messures, but it could still happen i just havent seen it happen after my fixes
