import os

"""
Notes:
    You can change number of maxium everyone and here mentions per day by changing the value in lines 189 (here) and 173 (everyone).
    You can change the slot rules in line 65
    You can pm me on discord (coolptqs) or telegram (@fedsfucker) for help or questions
    Don't forget to set your token and owner(s) ID(s) and other configuration in the config.json file
    Please follow my github and leave a star if you like the bot https://github.com/ptqsiscool
"""

try:
    import json
    import discord
    import asyncio
    import datetime
except ModuleNotFoundError:
    os.system('pip install -r requirements.txt')

from discord.ext import commands
from discord import Embed
from datetime import date, datetime, timedelta

command_usage = {}
slot_tasks = {}
slot_channels = {}

def load_cfg():
    load_config = json.load(open('config.json'))
    return load_config['token'], load_config['owner'], load_config['prefix'], load_config['slot_category']

token, owner, prefix, slot_category = load_cfg()
bot = commands.Bot(command_prefix=prefix, intents=discord.Intents.all(), help_command=None)

@bot.event
async def on_ready():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f'Slot Bot by @fedscuker | coolptqs (discord) | https://github.com/ptqsiscool\n\nLogged in as {bot.user.name}#{bot.user.discriminator} ({bot.user.id})\nPrefix: {prefix}\nOwner: {owner}\n')

@bot.command()
async def setslot(ctx, user: discord.Member, duration: str):
    if ctx.author.id not in owner:
        return
    if duration.endswith('w'):
        seconds = int(duration[:-1]) * 7 * 24 * 60 * 60
        slot_name = f'{user.name}-week-slot'
    elif duration.endswith('m'):
        seconds = int(duration[:-1]) * 30 * 24 * 60 * 60
        slot_name = f'{user.name}-month-slot'
    elif duration == 'lifetime':
        seconds = None
        slot_name = f'{user.name}-lifetime-slot'
    else:
        await ctx.send("`Invalid duration. Use 'w' for weeks, 'm' for months and 'lifetime' for infinite duration.`")
        return

    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
        user: discord.PermissionOverwrite(read_messages=True, send_messages=True, mention_everyone=False)
    }

    category = discord.utils.get(ctx.guild.categories, id=int(slot_category))
    if category is None:
        await ctx.send(f"`Category with ID '{slot_category}' not found.`")
        return
    channel = await category.create_text_channel(slot_name, overwrites=overwrites)

    await channel.send(f"{user.mention}\n\n`- You can't resell your slot`\n`- Scam = ban`\n`- 1 here and 1 everyone per day`\n`- Promote your server link is not authorized`")
    
    if seconds is not None:
        task = asyncio.create_task(end_slot(channel, user, seconds))
        slot_tasks[user.id] = task
    slot_channels[user.id] = channel.id

async def end_slot(channel, user, seconds):
    await asyncio.sleep(seconds)

    if not asyncio.current_task().cancelled():
        await channel.set_permissions(user, read_messages=True, send_messages=False)
        await channel.send(f'## {user.mention}, your slot has ended, open a ticket to continue or stop')

@bot.command()
async def addtime(ctx, user: discord.Member, duration: str):
    if ctx.author.id not in owner:
        return
    if duration.endswith('w'):
        seconds = int(duration[:-1]) * 7 * 24 * 60 * 60
    elif duration.endswith('m'):
        seconds = int(duration[:-1]) * 30 * 24 * 60 * 60
    elif duration.endswith('min'):
        seconds = int(duration[:-3]) * 60
    else:
        await ctx.send("Invalid duration. Use 'w' for weeks, 'm' for months, and 'min' for minutes.")
        return

    if user.id in slot_tasks:
        task = slot_tasks[user.id]
        if not task.done():
            task.cancel()
        channel = bot.get_channel(slot_channels[user.id])     
        await channel.set_permissions(user, read_messages=True, send_messages=True)
        new_task = asyncio.create_task(end_slot(channel, user, seconds))
        slot_tasks[user.id] = new_task
        await ctx.send(f"{user.mention}'s slot has been extended by {duration}.")
    else:
        await ctx.send(f"{user.mention} does not have a slot.")

@bot.command()
async def hold(ctx, user: discord.Member):
    if ctx.author.id not in owner:
        return
    if user.id in slot_channels:
        channel = bot.get_channel(slot_channels[user.id])
        await channel.set_permissions(user, read_messages=True, send_messages=False)
        embed = Embed(title="Slot Hold", description=f"{user.mention}'s slot has been put on hold. Don't buy from him since the problem is not solved.", color=0xFFD88E)
        embed.set_thumbnail(url="attachment://hold.png")
        await ctx.send(embed=embed, file=discord.File('img/hold.png'))
    else:
        embed = Embed(title="Error", description=f"{user.mention} does not have a slot.", color=0xe74c3c)
        await ctx.send(embed=embed)

@bot.command()
async def unhold(ctx, user: discord.Member):
    if ctx.author.id not in owner:
        return
    if user.id in slot_channels:
        channel = bot.get_channel(slot_channels[user.id])
        await channel.set_permissions(user, read_messages=True, send_messages=True)
        embed = Embed(title="Slot Unhold", description=f"{user.mention}'s slot has been released from hold.", color=0x2ecc71)
        embed.set_thumbnail(url="attachment://success.png")
        await ctx.send(embed=embed, file=discord.File('img/success.png'))
    else:
        embed = Embed(title="Error", description=f"{user.mention} does not have a slot.", color=0xe74c3c)
        await ctx.send(embed=embed)

@bot.command()
async def stop(ctx, user: discord.Member):
    if ctx.author.id not in owner:
        return
    if user.id in slot_channels:
        channel = bot.get_channel(slot_channels[user.id])
        await channel.delete()
        del slot_tasks[user.id]
        del slot_channels[user.id]

        await ctx.send(f"{user.mention}'s slot has been deleted.")
    else:
        await ctx.send(f"{user.mention} does not have a slot.")

@bot.command()
async def revoke(ctx, user: discord.Member, *, reason: str):
    if ctx.author.id not in owner:
        return
    if user.id in slot_channels:
        channel = bot.get_channel(slot_channels[user.id])
        await channel.set_permissions(user, read_messages=True, send_messages=False)
        del slot_tasks[user.id]
        del slot_channels[user.id]
        embed = Embed(title="Slot Revoked", description=f"{user.mention}'s slot has been revoked for the following reason\n\n`{reason}`", color=0xe74c3c)
        embed.set_thumbnail(url="attachment://stop.png")
        await ctx.send(embed=embed, file=discord.File('img/stop.png'))
        asyncio.create_task(delete_channel_after_delay(channel, 86400))
    else:
        embed = Embed(title="Error", description=f"{user.mention} does not have a slot.", color=0xe74c3c)
        await ctx.send(embed=embed)

async def delete_channel_after_delay(channel, delay):
    await asyncio.sleep(delay)
    await channel.delete()

@bot.command()
async def everyone(ctx):
    if ctx.author.id not in slot_channels:
        return
    today = date.today()

    if (ctx.author.id, today, 'everyone') in command_usage:
        if command_usage[(ctx.author.id, today, 'everyone')] >= 1:
            await ctx.send("`You have already used your @everyone for today.`")
            return
        else:
            command_usage[(ctx.author.id, today, 'everyone')] += 1
    else:
        command_usage[(ctx.author.id, today, 'everyone')] = 1
    await ctx.send("@everyone")

@bot.command()
async def here(ctx):
    if ctx.author.id not in slot_channels:
        return
    today = date.today()

    if (ctx.author.id, today, 'here') in command_usage:
        if command_usage[(ctx.author.id, today, 'here')] >= 1:
            await ctx.send("`You have already used your @here for today.`")
            return
        else:
            command_usage[(ctx.author.id, today, 'here')] += 1
    else:
        command_usage[(ctx.author.id, today, 'here')] = 1

    await ctx.send("@here")

@bot.command()
async def active_slots(ctx):
    if ctx.author.id not in owner:
        return

    embed = Embed(title="Active Slots", description="List of users with active slots", color=0x3498db)

    for user_id, task in slot_tasks.items():
        user = bot.get_user(user_id)
        channel = bot.get_channel(slot_channels[user_id])
        expiration_time = datetime.now() + timedelta(seconds=task.when())
        embed.add_field(name=f"{channel.name}", value=f"{user.mention} | {expiration_time.strftime('%d %b %Y %H:%M:%S')}", inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def help(ctx):
    embed = Embed(title="Slot Bot Help", description="Commands for the Slot Bot", color=0x7879F1)
    embed.add_field(name="setslot", value="`setslot <user> <duration>` - Set a slot for a user", inline=False)
    embed.add_field(name="addtime", value="`addtime <user> <duration>` - Add time to a user's slot", inline=False)
    embed.add_field(name="hold", value="`hold <user>` - Put a user's slot on hold", inline=False)
    embed.add_field(name="unhold", value="`unhold <user>` - Release a user's slot from hold", inline=False)
    embed.add_field(name="stop", value="`stop <user>` - Stop a user's slot", inline=False)
    embed.add_field(name="revoke", value="`revoke <user> <reason>` - Revoke a user's slot", inline=False)
    embed.add_field(name="everyone", value="`everyone` - Mention @everyone", inline=False)
    embed.add_field(name="here", value="`here` - Mention @here", inline=False)
    await ctx.send(embed=embed)

bot.run(token)