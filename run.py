from slackbot.bot import Bot
from slackbot.bot import respond_to

@respond_to('Give me (.*)')
def giveme(message, something):
    message.reply('Here is {}'.format(something))


def main():
    bot = Bot()
    bot.run()

if __name__ == "__main__":
    main()
