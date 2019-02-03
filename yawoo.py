'''A discord bot for college students.'''

import discord
import asyncio
import datetime
import random
import math
import time
import difflib
import pymongo
import os
import json
from discord.ext import commands
from urllib.request import urlopen, Request
from yawoo_secrets import token

__author__ = 'kaga'

prefix = '*'
bot = commands.Bot(command_prefix=prefix)
yawoo_folder = '/home/yawoo/YaWoo'
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
meta = '362687529004040193'
regulars = '501972625149526036'
mute_role = '434933653449998338'
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
    'schedule':[],
    'roles':[],
    'mr':False,
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
    profile = initialize(member.id)
    if profile['roles']:
        await bot.send_message(discord.Object(general), f'Welcome back, {member.mention}! <:Dude:449770873176719390>\
        \nYour roles have been reassigned.')
        await bot.add_roles(member, *(discord.Object(role) for role in profile['roles']))
        if profile['mr']:
            await bot.edit_channel_permissions(discord.Object(regulars), member, discord.PermissionOverwrite(read_messages=True))
        return
    welcome = await bot.send_file(discord.Object(general), colleges_file, content=f'Welcome to the University of Houston Discord server, {member.mention}! <:Dude:449770873176719390>\
        \n\nPlease pick your college from the list below:')
    for college_emote in college_emotes:
        await bot.add_reaction(welcome, college_emote)
    result = await bot.wait_for_reaction(college_emotes.keys(), user=member, message=welcome)
    await bot.add_roles(member, discord.Object(college_emotes[result.reaction.emoji]))
    await bot.send_message(discord.Object(general), f'{member.name} has joined {college_role.name}.')

@bot.event
async def on_member_remove(member):
    if member.server.id != uh_discord: return
    await bot.send_message(discord.Object(general), f'<a:crabRave:531589239998119956> {member.display_name} is gone <a:crabRave:531589239998119956>')

@bot.event
async def on_member_update(before, after):
    if before.roles != after.roles:
        profiles.update_one({'_id':after.id}, {'$set':{'roles':[role.id for role in after.roles]}})

@bot.event
async def on_channel_update(before, after):
    if after.id == regulars and after.overwrites != before.overwrites:
        reg_members = [ow[0].id for ow in after.overwrites if ow[1].read_messages and isinstance(ow[0], discord.Member)]
        profiles.update_many({'_id':{'$in':reg_members}}, {'$set':{'mr':True}})
        profiles.update_many({'_id':{'$not':{'$in':reg_members}}}, {'$set':{'mr':False}})

@bot.event
async def on_message(message):
    if message.author.bot: return
    if message.content.startswith(prefix):
        split = message.content.split()
        if split[-1].isdigit():
            quote_number = split[-1]
            split = split[:-1]
        else: quote_number = ''
        member_name = ' '.join(split[1:]) if split[0] == prefix + 'quote' else ' '.join(split)[1:]
        try:
            member_mention = next(member.mention for member in bot.get_server(uh_discord).members if member_name.lower() in (member.display_name.lower(), member.name.lower()))
            message.content = f'{prefix}quote {member_mention} {quote_number}'
        except StopIteration: pass
    await bot.process_commands(message)

@bot.event
async def on_message_delete(message):
    if not message.server or message.server.id != uh_discord or message.author.bot: return
    mod_delete = any(reaction for reaction in message.reactions if reaction.emoji == delete_emoji)
    embed = discord.Embed(description=message.content, color=embed_color)
    embed.set_author(name=f'Message by {message.author.display_name} was {"stealth " if mod_delete else ""}deleted', icon_url=message.author.avatar_url)
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
    await bot.process_commands(after)
    ratio = difflib.SequenceMatcher(None, before.content, after.content).ratio()
    if ratio > .9: return
    embed = discord.Embed(color=embed_color)
    embed.set_author(name=f'Message edited by {before.author.display_name}', icon_url=before.author.avatar_url)
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
            await bot.send_message(reaction.message.channel, f'You can\'t quote yourself! {error}')
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
        await bot.send_message(reaction.message.channel, f'{target.display_name} had their {quote_number}{suffix} quote added by {member.display_name}.')
        embed = discord.Embed(title=f'Message by {target.display_name} was quoted by {member.display_name}', description=quote['content'], color=embed_color)
        embed.set_image(url=quote['attachment'])
        embed.add_field(name='Number', value=str(quote_number)).add_field(name='Channel', value=reaction.message.channel.mention)
        await bot.send_message(discord.Object(chat_log), embed=embed)

@bot.event
async def on_command_error(e, ctx):
    if isinstance(e, commands.CommandOnCooldown):
        message = await bot.send_message(ctx.message.channel, f'This command is on cooldown for {round(e.retry_after)+1} more second(s). {error}')
        await bot.add_reaction(message, delete_emoji)
    elif isinstance(e, commands.CheckFailure):
        await bot.send_message(ctx.message.channel, f'You\'re unable to do that! {error}')
    else: print(e)

@bot.command(pass_context=True)
async def ping(ctx):
    '''Check the bot's response time.'''
    start = time.time()
    message = await bot.say('My ping is...')
    await asyncio.sleep(3)
    end = time.time()
    await bot.edit_message(message, f'My ping is... **{round((end-start-3)*1000, 2)}** milliseconds.')

@bot.command(pass_context=True, aliases=['eval'])
@commands.cooldown(1, 5, commands.BucketType.user)
async def calc(ctx, *expression: str):
    '''Calculate any python expression.'''
    member = ctx.message.author
    try:
        globals = {
            'datetime':datetime,
            'random':random,
            'math':math,
            'uh':bot.get_server(uh_discord),
        }
        is_staff = hasattr(member, 'roles') and any(role.id in staff_role_ids.values() for role in member.roles)
        if is_staff:
            globals['profiles'] = profiles
            globals['bot'] = bot
        result = str(eval(' '.join(expression), globals, None))
        if not is_staff and len(result) > 500: await bot.say(f'Stop spamming! {error}')
        else: await bot.say(result)
    except Exception as e: await bot.say(f'Error: {e}. {error}')

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
        await bot.say(f'{target.display_name} has no quotes added. {error}')
        return
    def make_quote_embed(number):
        if number < 0: raise IndexError
        quote = target_profile['quotes'][number]
        quote_embed = discord.Embed(description=quote['content'], color=embed_color, timestamp=quote['timestamp'])
        quote_embed.set_image(url=quote['attachment'])
        number += 1
        suffix = {1:'st', 2:'nd', 3:'rd'}.get(number % 10, 'th') if number % 100 < 10 or 20 < number % 100 else 'th'
        if target: quote_embed.set_author(name='{0}{1} quote from {2.display_name}'.format(number, suffix, target), icon_url=target.avatar_url)
        return quote_embed
    number = (number - 1) if number else random.randrange(len(target_profile['quotes']))
    try:
        quote_msg = await bot.say(embed=make_quote_embed(number))
    except IndexError:
        await bot.say(f'{target.display_name} only has {len(target_profile["quotes"])} quote(s). {error}')
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
async def locations(ctx):
    '''Check what dining locations are currently open on campus.'''
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-6)))
    loading = await bot.say('<a:nowLoading:500000449949204495> Fetching locations, please wait <a:nowLoading:500000449949204495>')
    req = Request(f'https://api.dineoncampus.com/v1/locations/open?site_id=5925f42eee596f0f95969b10&timestamp={now.isoformat()}')
    with urlopen(req) as res:
        locations = json.loads(res.read())['location_schedules']
    await bot.delete_message(loading)
    open_locations = '__**All Open Dining Locations:**__\n'
    for location in locations:
        try: schedule = next(schedule for schedule in location['schedules'] if now.isoweekday() in schedule['days'])
        except StopIteration: continue
        start_time = datetime.time(schedule['start_hour'], schedule['start_minutes'])
        end_time = datetime.time(schedule['end_hour'], schedule['end_minutes'])
        if start_time < now.time() < end_time:
            open_locations += f'\n- {location["name"]} closes at {end_time.strftime("%I:%M %p")}'
    await bot.say(open_locations)

@bot.command(pass_context=True, aliases=['moodyswipe'])
async def moody(ctx):
    '''See what Moody Towers dining hall has on the menu.'''
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-6)))
    loading = await bot.say('<a:nowLoading:500000449949204495> Fetching menu, please wait <a:nowLoading:500000449949204495>')
    req = Request(f'https://api.dineoncampus.com/v1/location/menu?site_id=5925f42eee596f0f95969b10&platform=0&location_id=59b2b6e2ee596fc4596321b0&date={now.strftime("%y-%m-%d")}')
    with urlopen(req) as res:
        menu = json.loads(res.read())['menu']['periods']
    await bot.delete_message(loading)
    now_t = now.time()
    if now_t < datetime.time(7) or datetime.time(22) < now_t:
        await bot.say('Sorry, there\'s nothing to display at this time.')
        return
    period = (menu[0] if datetime.time(7) < now_t < datetime.time(11) else
              menu[1] if datetime.time(11) < now_t < datetime.time(17) else
              menu[2])
    categories_menu = 'Choose a food category to see what\'s available:\n'
    categories_menu += '\n'.join(f':white_small_square: {i}) {cat["name"]} ({len(cat["items"])} item(s) available)' for i, cat in enumerate(period['categories'], 1))
    categories_msg = await bot.say(categories_menu)
    res = await bot.wait_for_message(timeout=20, author=ctx.message.author, channel=ctx.message.channel, check=lambda m:m.content.isdigit())
    await bot.delete_message(categories_msg)
    if res is None or int(res.content)-1 not in range(len(period['categories'])):
        await bot.say(f'You need to pick a category from the list. {error}')
        return
    await bot.add_reaction(res, delete_emoji)
    category = period['categories'][int(res.content)-1]
    items_emb = discord.Embed(title=f'Moody {period["name"]} Items in the {category["name"]} Category', color=embed_color)
    for item in category['items'][:20]:
        nutrients = f'{item["nutrients"][0]["value"]} cals, {item["nutrients"][4]["value"]}g protein, {item["nutrients"][8]["value"]}g carbs'
        items_emb.add_field(name=item['name'], value=nutrients)
    await bot.say(embed=items_emb)

@bot.command(pass_context=True)
@commands.has_any_role(*staff_role_ids)
async def unquote(ctx, target: discord.Member, num: int):
    '''Remove a quote from someone.'''
    target_profile = initialize(target.id)
    target_profile['quotes'].pop(num-1)
    profiles.update_one({'_id':target.id}, {'$set':{'quotes':target_profile['quotes']}})
    await bot.say(f'{target.display_name}\'s quote has been removed.')

@bot.command(pass_context=True)
@commands.has_any_role(*staff_role_ids)
async def prune(ctx, num: int, target: discord.Member = None):
    '''Remove a certain number of messages, with an optional user filter.'''
    if num > max_prune:
        await bot.say(f'You can only prune up to {max_prune} messages at a time. {error}')
        return
    async for message in bot.logs_from(ctx.message.channel, num + 1):
        if target and message.author != target: continue
        await bot.add_reaction(message, delete_emoji)
    await bot.say(f'{target.display_name}\'s messages were pruned.' if target else f'The last {num} messages were pruned.')
    await bot.send_message(discord.Object(chat_log), embed=discord.Embed(description=f'Messages from {ctx.message.channel.mention} were pruned', color=embed_color))

@bot.command(pass_context=True, aliases=['ban'])
@commands.has_any_role(*staff_role_ids)
async def mute(ctx, *targets: discord.Member):
    '''Mute any number of users at once.'''
    member = ctx.message.author
    if not targets:
        await bot.say(f'You need to give a user! {error}')
        return
    await bot.add_reaction(ctx.message, delete_emoji)
    for target in targets: await bot.add_roles(target, discord.Object(mute_role))
    if len(targets) == 1: await bot.send_message(discord.Object(meta), f'{targets[0].display_name} was muted by {member.display_name}.')
    else: await bot.send_message(discord.Object(meta), f'{member.display_name} muted multiple users:\n- {{}}'.format('\n- '.join(target.display_name for target in targets)))

@bot.command(pass_context=True, aliases=['unban'])
@commands.has_any_role(*staff_role_ids)
async def unmute(ctx, *targets: discord.Member):
    '''Unmute any number of users at once.'''
    member = ctx.message.author
    if not targets:
        await bot.say(f'You need to give a user! {0}')
        return
    await bot.add_reaction(ctx.message, delete_emoji)
    for target in targets: await bot.remove_roles(target, discord.Object(mute_role))
    if len(targets) == 1: await bot.send_message(discord.Object(meta), f'{targets[0].display_name} was unmuted by {member.display_name}.')
    else: await bot.send_message(discord.Object(meta), f'{member.display_name} unmuted multiple users:\n- {{}}'.format('\n- '.join(target.display_name for target in targets)))
@bot.command()
@commands.has_any_role(*staff_role_ids)
async def invites():
    '''Check invites in the server.'''
    invites = await bot.invites_from(bot.get_server(uh_discord))
    await bot.say('All invites:\n'+', '.join(f'{invite.inviter.name}: {invite.uses} uses' for invite in sorted(invites, key=lambda i:i.uses, reverse=True) if invite.uses > 0))

if __name__ == '__main__':
    bot.run(token)
