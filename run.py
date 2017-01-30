import random
from slackbot.bot import Bot
from slackbot.bot import respond_to

wordpath = '/opt/words/wordlist.txt'

with open(wordpath) as w:
    wordlist = w.readlines()

maybe = []
for word in wordlist:
    maybe.append(word.strip())


def generate_password():
    random.shuffle(maybe)
    newpass = maybe[0] + str(random.randint(0, 99)) + maybe[1] + str(random.randint(0, 99)) + maybe[2]
    return newpass


@respond_to('Give me (.*)')
def giveme(message, something):
    message.reply('Here is {}'.format(something))

@respond_to('password')
def pass_request(message):
    message.reply(generate_password)


def main():
    bot = Bot()
    bot.run()

if __name__ == "__main__":
    main()
