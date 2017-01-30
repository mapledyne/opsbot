@respond_to('password')
def pass_request(message):
    message.reply(generate_password())


@respond_to('admins')
def pass_request(message):
    message.reply('My admins are: {}'.format(", ".join(people['admins'])))
