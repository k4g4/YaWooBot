import discord
import asyncio
import datetime
import random
import math
import time
import difflib
import pymongo
import os
from discord.ext import commands

__author__ = 'kaga'

prefix = '*'
bot = commands.Bot(command_prefix=prefix)
token = ''
yawoo_folder = '/home/onahole/YaWoo'
colleges_file = os.path.join(yawoo_folder, 'colleges.png')
error = ':no_entry_sign:'
delete_timeout = 10
quote_timeout = 30
max_prune = 200
embed_color = 0xff1a1a
kaga = '204830788729044992'
moopy = '471538787760078860'
oblivion = '141022941230923776'
unaweona = '437400059022278657'
uh_discord = '362623183146188802'
chat_log = '504139294168842250'
general = '362623183146188804'
botspam = '362625628094070784'
delete_emoji = '🗑'
pin_emoji = '📌'
staff_role_ids = {
    'Admin':'362683637428387842',
    'Moderator':'362683270720258058',
    'Bot Commander':'363019947971969025',
    'Bots':'497118854435307520',
}
college_emotes = {
    '📑':'362632135481360384',
    '🎭':'362632220717875210',
    '💼':'362632359599800341',
    '🛠':'362632437177647107',
    '🖥':'362632615381041153',
    '🔢':'362632676751966210',
    '🏫':'505045074430656513',
    '🏨':'506324634115899393',
}

connection = pymongo.MongoClient("mongodb://localhost")
profiles = connection.uni.profiles
starter = {
    'quotes':[],
}

def initialize(id):
    return profiles.find_one_and_update({'_id':id}, {'$setOnInsert':starter}, upsert=True, return_document=pymongo.ReturnDocument.AFTER)

@bot.event
async def on_ready():
    print('''
+-------------------------+
| yawoo.exe has logged in |
+-------------------------+

    ''')

@bot.event
async def on_member_join(member):
    if member.server.id != uh_discord: return
    welcome = await bot.send_file(discord.Object(general), colleges_file, content='Welcome to the University of Houston Discord server, {0.mention}! <:Dude:449770873176719390>\
    \n\nPlease pick your college from the list below:'.format(member))
    for college_emote in college_emotes:
        await bot.add_reaction(welcome, college_emote)
    result = await bot.wait_for_reaction(college_emotes.keys(), user=member, message=welcome)
    college_role = [role for role in member.server.roles if role.id == college_emotes[result.reaction.emoji]][0]
    await bot.add_roles(member, college_role)
    await bot.send_message(discord.Object(general), '{0.name} has joined {1.name}.'.format(member, college_role))

@bot.event
async def on_member_remove(member):
    if member.server.id != uh_discord: return
    await bot.send_message(discord.Object(general), 'Sorry to see you go, {0.name}. <:receivepls:495699144250359829>'.format(member))

@bot.event
async def on_message(message):
    if message.author.bot: return
    if message.author.id == oblivion:
        if 'vanessa' in message.content.lower() or 'weona' in message.content.lower() or unaweona in message.content:
            await bot.add_reaction(message, delete_emoji)
    if '//skribbl.io/' in message.content:
        await bot.add_reaction(message, delete_emoji)
    if message.content.startswith(prefix):
        split = message.content.split()
        if split[-1].isdigit():
            quote_number = split[-1]
            split = split[:-1]
        else: quote_number = ''
        member_name = ' '.join(split[1:]) if split[0] == prefix + 'quote' else ' '.join(split)[1:]
        try:
            member_mention = next(member.mention for member in bot.get_server(uh_discord).members if member_name.lower() in (member.display_name.lower(), member.name.lower()))
            message.content = '{0}quote {1} {2}'.format(prefix, member_mention, quote_number)
        except StopIteration: pass
    await bot.process_commands(message)

@bot.event
async def on_message_delete(message):
    if not message.server or message.server.id != uh_discord or message.author.bot: return
    mod_delete = any(reaction for reaction in message.reactions if reaction.emoji == delete_emoji)
    embed = discord.Embed(description=message.content, color=embed_color)
    embed.set_author(name='Message by {0.author.display_name} was {1}deleted'.format(message, 'stealth ' if mod_delete else ''), icon_url=message.author.avatar_url)
    if message.attachments: embed.add_field(name='Filename', value=message.attachments[0]['filename'])
    if not mod_delete: revived_message = await bot.send_message(message.channel, embed=embed)
    embed.add_field(name='Channel', value=message.channel.mention)
    embed.timestamp = message.timestamp
    await bot.send_message(discord.Object(chat_log), embed=embed)
    await asyncio.sleep(delete_timeout)
    if not mod_delete: await bot.delete_message(revived_message)

@bot.event
async def on_message_edit(before, after):
    if not before.server or before.server.id != uh_discord or before.author.bot: return
    ratio = difflib.SequenceMatcher(None, before.content, after.content).ratio()
    if ratio > .9: return
    embed = discord.Embed(color=embed_color)
    embed.set_author(name='Message edited by {0.author.display_name}'.format(before), icon_url=before.author.avatar_url)
    embed.add_field(name='Before', value=before.content).add_field(name='After', value=after.content)
    revived_message = await bot.send_message(before.channel, embed=embed)
    embed.add_field(name='Channel', value=before.channel.mention)
    embed.timestamp = before.timestamp
    await bot.send_message(discord.Object(chat_log), embed=embed)
    await asyncio.sleep(delete_timeout)
    await bot.delete_message(revived_message)

@bot.event
async def on_reaction_add(reaction, member):
    if member.server.id != uh_discord: return
    if reaction.emoji == delete_emoji and hasattr(member, 'roles') and any(role.id in staff_role_ids.values() for role in member.roles):
        await bot.delete_message(reaction.message)
    if any(reaction.emoji == pin_emoji and reaction.count == 1 for reaction in reaction.message.reactions):
        if 'nigger' in reaction.message.content.lower():
            return
        target = reaction.message.author
        if target == member:
            await bot.send_message(reaction.message.channel, 'You can\'t quote yourself! {0}'.format(error))
            return
        quote = {
            'id':reaction.message.id,
            'timestamp':reaction.message.timestamp,
            'content':reaction.message.content,
            'attachment':reaction.message.attachments[0]['url'] if reaction.message.attachments else ''
        }
        target_profile = initialize(target.id)
        if reaction.message.id in (quote['id'] for quote in target_profile['quotes']):
            return
        profiles.update_one({'_id':target.id}, {'$push':{'quotes':quote}})
        quote_number = len(target_profile['quotes']) + 1
        suffix = {1:'st', 2:'nd', 3:'rd'}.get(quote_number % 10, 'th') if quote_number % 100 < 10 or 20 < quote_number % 100 else 'th'
        await bot.send_message(reaction.message.channel, '{0.display_name} had their {1}{2} quote added by {3.display_name}.'.format(target, quote_number, suffix, member))
        embed = discord.Embed(title='Message by {0.display_name} was quoted by {1.display_name}'.format(target, member), description=quote['content'], color=embed_color)
        embed.set_image(url=quote['attachment'])
        embed.add_field(name='Number', value=str(quote_number)).add_field(name='Channel', value=reaction.message.channel.mention)
        await bot.send_message(discord.Object(chat_log), embed=embed)

@bot.event
async def on_command_error(e, ctx):
    if isinstance(e, commands.CommandOnCooldown):
        cd = round(e.retry_after) + 1
        message = await bot.send_message(ctx.message.channel, 'This command is on cooldown for {0:d} more second(s). {1}'.format(cd, error))
    elif isinstance(e, commands.CheckFailure):
        message = await bot.send_message(ctx.message.channel, 'You\'re unable to do that! {0}'.format(error))
    else: print(e)
    await asyncio.sleep(5)
    await bot.add_reaction(message, delete_emoji)
    await bot.add_reaction(ctx.message, delete_emoji)

@bot.command(pass_context=True)
async def ping(ctx):
    '''Check the bot's response time.'''
    t1 = time.perf_counter()
    await bot.send_typing(ctx.message.author)
    t2 = time.perf_counter()
    ping = int((t2-t1) * 1000)
    await bot.say('My ping is **{0:d}** milliseconds.'.format(ping))

@bot.command(pass_context=True)
@commands.cooldown(1, 5, commands.BucketType.user)
async def calc(ctx, *expression: str):
    '''Calculate any python expression.'''
    try:
        globals = {
            'datetime':datetime,
            'random':random,
            'math':math,
            'uh':bot.get_server(uh_discord),
        }
        is_staff = any(role.id in staff_role_ids.values() for role in ctx.message.author.roles)
        if is_staff:
            globals['profiles'] = profiles
            globals['bot'] = bot
        result = str(eval(' '.join(expression), globals, None))
        if not is_staff and len(result) > 500: await bot.say('Stop spamming! {0}'.format(error))
        else: await bot.say(result)
    except Exception as e: await bot.say('Error: {0}. {1}'.format(e, error))

@bot.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def cocoa(*text: str):
    '''Type in cocoatext!'''
    await bot.say(''.join('<:{0.name}:{0.id}>'.format(discord.utils.get(bot.get_all_emojis(), name='_' + c.lower() if c.isalpha() else 'space')) for c in ' '.join(text)))

@bot.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def dance(*text: str):
    '''Dancing letters.'''
    await bot.say(''.join('<a:{0.name}:{0.id}>'.format(discord.utils.get(bot.get_all_emojis(), name=c.lower() + '_dance' if c.isalpha() else 'transparent')) for c in ' '.join(text)))

@bot.command(pass_context=True, aliases=['getquote'])
@commands.cooldown(3, 20, commands.BucketType.user)
async def quote(ctx, target: discord.Member = None, number: int = None):
    '''Bring up a quote from another user. If no user is tagged, one is picked at random.'''
    if target is None:
        target_profile = next(profiles.aggregate([{'$match':{'quotes':{'$not':{'$size':0}}}}, {'$sample':{'size':1}}]))
        try: target = ctx.message.server.get_member(target_profile['_id'])
        except: target = None
    else: target_profile = initialize(target.id)
    if not target_profile['quotes']:
        await bot.say('{0.display_name} has no quotes added. {1}'.format(target, error))
        return
    def make_quote_embed(number):
        if number < 0: raise IndexError
        quote = target_profile['quotes'][number]
        quote_embed = discord.Embed(description='{}'.format(quote['content']), color=embed_color, timestamp=quote['timestamp'])
        quote_embed.set_image(url=quote['attachment'])
        number += 1
        suffix = {1:'st', 2:'nd', 3:'rd'}.get(number % 10, 'th') if number % 100 < 10 or 20 < number % 100 else 'th'
        if target: quote_embed.set_author(name='{0}{1} quote from {2.display_name}'.format(number, suffix, target), icon_url=target.avatar_url)
        return quote_embed
    number = (number - 1) if number else random.randrange(len(target_profile['quotes']))
    try:
        quote_msg = await bot.say(embed=make_quote_embed(number))
    except IndexError:
        await bot.say('{0.display_name} only has {1} quote(s). {2}'.format(target, len(target_profile['quotes']), error))
        return
    await bot.add_reaction(quote_msg, '⬅')
    await bot.add_reaction(quote_msg, '⏸')
    await bot.add_reaction(quote_msg, '➡')
    while True:
        response = await bot.wait_for_reaction(('⬅', '⏸', '➡'), timeout=quote_timeout, message=quote_msg, check=lambda r, u: not u.bot)
        if not response or response.reaction.emoji == '⏸': break
        await bot.remove_reaction(quote_msg, response.reaction.emoji, response.user)
        number += 1 if response.reaction.emoji == '➡' else -1
        try:
            await bot.edit_message(quote_msg, embed=make_quote_embed(number))
        except IndexError: pass
    await bot.clear_reactions(quote_msg)

@bot.command(pass_context=True)
@commands.has_any_role(*staff_role_ids)
async def unquote(ctx, target: discord.Member, num: int):
    '''Remove a quote from someone.'''
    target_profile = initialize(target.id)
    target_profile['quotes'].pop(num-1)
    profiles.update_one({'_id':target.id}, {'$set':{'quotes':target_profile['quotes']}})
    await bot.say('{0.display_name}\'s quote has been removed.'.format(target))

@bot.command(pass_context=True)
@commands.has_any_role(*staff_role_ids)
async def prune(ctx, num: int, target: discord.Member = None):
    '''Remove a certain number of messages, with an optional user filter.'''
    if num > max_prune:
        await bot.say('You can only prune up to {0} messages at a time. {1}'.format(max_prune, error))
        return
    async for message in bot.logs_from(ctx.message.channel, num + 1):
        if target and message.author != target: continue
        await bot.add_reaction(message, delete_emoji)
    message = await bot.say('{0.display_name}\'s messages were pruned.'.format(target) if target else 'The last {0} messages were pruned.'.format(num))
    await bot.send_message(discord.Object(chat_log), '{0.content}\nChannel: {0.channel.mention}'.format(message))
    await asyncio.sleep(delete_timeout)
    await bot.add_reaction(message, delete_emoji)

@bot.command()
@commands.has_any_role(*staff_role_ids)
async def invites():
    '''Check invites in the server.'''
    invites = await bot.invites_from(bot.get_server(uh_discord))
    await bot.say('All invites:\n'+', '.join('{0.inviter.name}: {0.uses} uses'.format(invite) for invite in sorted(invites, key=lambda i:i.uses, reverse=True) if invite.uses > 0))

async def loop():
    pass

if __name__ == '__main__':
    bot.loop.create_task(loop())
    bot.run(token)
