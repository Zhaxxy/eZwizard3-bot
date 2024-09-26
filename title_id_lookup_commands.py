import asyncio
from typing import Sequence, Generator
import re
import logging
import sqlite3
from typing import Any
import dis

from interactions import Extension, slash_command, SlashContext, slash_option, SlashCommandChoice, OptionType, AutocompleteContext, Embed, Client
from rapidfuzz import fuzz, utils

from data_files import KNOWN_TITLE_IDS, KNOWN_REGIONS, REGION_EMOJIS
try:
    from bot_admin_helpers import is_in_test_mode, is_in_fast_boot_mode
except ModuleNotFoundError:
    logging.warn('Could not find `bot_admin_helpers` to check if bot is in test mode, so dm when bot online has been disabled')
    DM_PEOPLE_WHEN_ONLINE = False
else:
    DM_PEOPLE_WHEN_ONLINE = True

try:
    from title_id_lookup_commands_admins import BOT_ADMINS
except ModuleNotFoundError:
    logging.warn('Could not find `title_id_lookup_commands_admins` to check for bot_admins, so /admin_server_list wont work')
    BOT_ADMINS = ()



ERROR_SIDE_EMBED_COLOUR = 0xFF0000
NORMAL_EMBED_COLOUR = 0x00FF00

CUSA_TITLE_ID = re.compile(r'CUSA\d{5}') # This already exists in string_helpers, but i dont want this to rely on anything besides data_files

if not 'United Kingdom' in KNOWN_REGIONS:
    raise AssertionError(f'Exepcted United Kingdom to be in {KNOWN_REGIONS}')
if not 'England' not in KNOWN_REGIONS:
    raise AssertionError(f'Exepcted England to not to be in {KNOWN_REGIONS}')
REGION_SLASH_OPTIONS = tuple(
        dict(name=region, value=region) for region in KNOWN_REGIONS
        ) + (dict(name='England', value='United Kingdom'),)

TOO_MANY_GAMES_EMBED = Embed(
        title = 'Found too many games',
        description = f'Please be more spefic with your search, or by setting the optional `fuzz_score_to_match` higher',
        footer = 'If you put all regions, perhaps try putting one, like Europe or France',
        color = ERROR_SIDE_EMBED_COLOUR
    )

NO_GAMES_FOUND_EMBED = Embed(
        title = 'No games found',
        description = f'Make sure you are spelling the game correctly, or by setting the optional `fuzz_score_to_match` lower',
        footer = 'Perhaps try being more broad with the region, such as searching by Europe instead of Germany',
        color = ERROR_SIDE_EMBED_COLOUR
    )


def chunker(seq, size):
    """
    https://stackoverflow.com/questions/434287/how-to-iterate-over-a-list-in-chunks
    """
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


def title_id_embed_gen(title_id: str, game_name: str, regions: Sequence[str]) -> Embed:
    serial_station_url = f'https://www.serialstation.com/titles/{title_id[:4]}/{title_id[4:]}'
    title_id_embed = Embed(title = game_name,url = serial_station_url, description = title_id, color = NORMAL_EMBED_COLOUR, footer = 'All data is from SerialStation!')
    for region in regions:
        title_id_embed.add_field(region,REGION_EMOJIS[region],inline=True)
    return title_id_embed


def title_id_not_found_embed_gen(title_id: str) -> Embed:
    return Embed(
        title = f'{title_id} was not found',
        description = f'Maybe you typed the numbers wrong?',
        footer = 'If you know for certain this title id exists, please report the title id and what game it should be, perhaps its a new game',
        color = ERROR_SIDE_EMBED_COLOUR
    )


_ALREADY_INIT_DM_ME_WHEN_ONLINE_USERS_DATABASE = False
def init_dm_me_when_online_users_database() -> None:
    global _ALREADY_INIT_DM_ME_WHEN_ONLINE_USERS_DATABASE
    if _ALREADY_INIT_DM_ME_WHEN_ONLINE_USERS_DATABASE:
        return
    try:
        conn = sqlite3.connect('dm_me_when_online_users.db')
        cur = conn.cursor()

        cur.execute('''
            CREATE TABLE IF NOT EXISTS dm_me_when_online_users (
                id INTEGER PRIMARY KEY
            )
        ''')
        conn.commit()
        _ALREADY_INIT_DM_ME_WHEN_ONLINE_USERS_DATABASE = True
    finally:
        conn.close()

DM_ME_WHEN_ONLINE_DB_LOCK = asyncio.Lock()

def add_user_to_dm_when_online_list(author_id: int):
    try:
        conn = sqlite3.connect('dm_me_when_online_users.db')
        cur = conn.cursor()

        cur.execute('INSERT INTO dm_me_when_online_users (id) VALUES (?)',(author_id,))
        conn.commit()
    finally:
        conn.close()
# TODO, look into using threading to be safe
def is_user_in_dm_when_online_list(author_id: int) -> bool:
    try:
        conn = sqlite3.connect('dm_me_when_online_users.db')
        cur = conn.cursor()

        cur.execute('SELECT id FROM dm_me_when_online_users WHERE id = ?', (author_id,))
        return cur.fetchone() is not None
    finally:
        conn.close()

def remove_user_to_dm_when_online_list(author_id: int):
    try:
        conn = sqlite3.connect('dm_me_when_online_users.db')
        cur = conn.cursor()

        cur.execute('DELETE FROM dm_me_when_online_users WHERE id = ?',(author_id,))
        conn.commit()
    finally:
        conn.close()

def fetch_all_dmers_wanters() -> Generator[int,None,None]:
    try:
        conn = sqlite3.connect('dm_me_when_online_users.db')
        cur = conn.cursor()

        cur.execute('SELECT id FROM dm_me_when_online_users')
        for x in cur.fetchall():
            yield x[0]
    finally:
        conn.close()

def _is_admin(author_id: int) -> bool:
    return author_id in BOT_ADMINS
    
async def dm_all_at_once(bot: Client) -> None:
    if is_in_test_mode():
        return
    if not DM_PEOPLE_WHEN_ONLINE:
        return
    init_dm_me_when_online_users_database()
    for author_id in fetch_all_dmers_wanters():
        author = await bot.fetch_user(author_id)
        if not author:
            pass#logging.debug(f'Could not find {author_id} for dming, skipping')
            continue
        
        try:
            await author.send(f'<@{author_id}> I am online, use me quick! (if you dont want to get any DMs from this bot anymore, run `/dm_me_when_online` again)')
        except Exception as e:
            pass#logging.debug(f'Could not dm {author_id}, got error {e}, skipping')
        
        pass#logging.debug(f'Dmed {author_id} succsfully!')


class CouldNotEvalConstatCause2Large(Exception):
    """
    A
    """

def get_cool_thing(thing: str) -> Any:
    me = eval(f'lambda: {thing}')
    try:
        me = me[0]
    except Exception:
        pass
    results = [x.argrepr for x in dis.get_instructions(me) if x.opname in ('LOAD_CONST','LOAD_GLOBAL')]
    if len(results) != 1:
        raise CouldNotEvalConstatCause2Large
    return results[0]


class TitleIdLookupCommands(Extension):
    @slash_command(name = 'game_lookup', description = 'Find all title ids based on game name')
    @slash_option(name='game_name',
        description='The name of the game to lookup',
        opt_type=OptionType.STRING,
        required=True,
        )
    @slash_option(name='region',
        description='The region of the game you want',
        opt_type=OptionType.STRING,
        required=True,
        autocomplete=True
        )
    @slash_option(name='fuzz_score_to_match',
        description='The lower this number, the more title ids it will find, default 95',
        opt_type=OptionType.NUMBER,
        min_value = 0.0,
        max_value = 100.0,
        required=False
        )
    async def find_title_ids_base_on_game_name(self,ctx: SlashContext,game_name: str, region: str | None, fuzz_score_to_match: float = 95.0):
        if region == 'All regions':
            region = None
        else:
            if region not in KNOWN_REGIONS:
                return await ctx.send('Please enter a region of the choice from the bot')
        
        found_things = set()
        for title_id,game_name_and_region in KNOWN_TITLE_IDS.items():
            if len(found_things) > 10:
                return await ctx.send(embed=TOO_MANY_GAMES_EMBED)
            if fuzz.QRatio(game_name_and_region[0], game_name, processor=utils.default_process) >= fuzz_score_to_match:
                if (not region or region in game_name_and_region[1]):
                    found_things.add((f'CUSA{title_id:05}',*game_name_and_region))
        if not found_things:
            return await ctx.send(embed=NO_GAMES_FOUND_EMBED)
        return await ctx.send(embeds = [title_id_embed_gen(*x) for x in found_things])
        
    @find_title_ids_base_on_game_name.autocomplete('region')
    async def find_title_ids_base_on_game_name_autocomplete(self,ctx: AutocompleteContext):
        string_option_input = ctx.input_text
        if not string_option_input:
            return await ctx.send(choices=[{'name':'All regions','value':'All regions'}])
        string_option_input = string_option_input.lower()
        
        
        return await ctx.send(choices=[x for x in REGION_SLASH_OPTIONS if string_option_input in x['name'].lower()])
    
    @slash_command(name = 'title_id_lookup', description = 'Get game and region from title id')
    @slash_option(name='title_id',
        description='The title id of the game (starting with CUSA)',
        opt_type=OptionType.STRING,
        required=True,
        max_length = 4 + 5,
        min_length = 4 + 5,
        )
    async def find_game_based_on_title_id(self,ctx: AutocompleteContext, title_id: str):
        title_id = title_id.upper()
        if not CUSA_TITLE_ID.fullmatch(title_id):
            return await ctx.send(f'Invalid title id {title_id}')
        
        try:
            game_name_and_region = KNOWN_TITLE_IDS[int(title_id[4:])]
        except KeyError:
            return await ctx.send(embed=title_id_not_found_embed_gen(title_id))
        
        return await ctx.send(embed = title_id_embed_gen(title_id,*game_name_and_region))
    if DM_PEOPLE_WHEN_ONLINE:
        @slash_command(name = 'dm_me_when_online', description = 'Toggle on and off if you want to get dmed when the bot is online')
        async def do_dm_me_when_online(self,ctx: AutocompleteContext):
            await ctx.defer()
            async with DM_ME_WHEN_ONLINE_DB_LOCK:
                if not is_user_in_dm_when_online_list(int(ctx.author_id)):
                    try:
                        await ctx.author.send('Test')
                    except Exception:
                        await ctx.send('Could not dm you, maybe you have dms disabled?')
                    add_user_to_dm_when_online_list(int(ctx.author_id))
                    await ctx.send('You will now get dmed by me, when I next go online! (run this command again to disable this)')
                else:
                    remove_user_to_dm_when_online_list(int(ctx.author_id))
                    await ctx.send('No longer, shall you get DMs by me! (run this command again to enable this)')

    # Made by smok (and chatgpt lol), and some edits by Zhaxxy
    @slash_command(
        name='admin_server_list', 
        description="Displays a list of all servers the bot is in. Admin only."
    )
    async def admin_server_list(self, ctx: SlashContext):
        if not _is_admin(ctx.author.id):
            await ctx.send(f"**Yo!**\n*You don't need to know this information..*", ephemeral=False)
            return

        guilds = ctx.bot.guilds
        guild_list = [f"• {guild.name} (ID: {guild.id})" for guild in guilds]
        guild_count = len(guilds)
        
        for sub_guild_list in chunker(guild_list,10):
            embed = Embed(
                title="📡 Lista de Servidores!",
                description=(
                    f"• **Numero de Servidores:** `{guild_count}`\n"
                    + "\n".join(sub_guild_list) + "\n\n"
                    f"To remove a server, use `/remove_server <guild_id>`."
                ),
                color=0x0083ff  # Customize the color if needed
            )

            await ctx.send(embed=embed, ephemeral=False)


    # Command to remove a server from the bot by typing the guild ID
    @slash_command(
        name='remove_server', 
        description="Removes the bot from the specified server. Admin only."
    )
    @slash_option("guild_id", description="The ID of the server to remove", opt_type=OptionType.STRING, required=True)
    async def remove_server(self, ctx: SlashContext, guild_id: str):
        if not _is_admin(ctx.author.id):
            await ctx.send("You do not have permission to use this command.", ephemeral=False)
            return
        try:
            guild_id = int(guild_id)
        except ValueError:
            guild = None
        else:
            guild = ctx.bot.get_guild(guild_id)
        
        if guild:
            await guild.leave()
            await ctx.send(f"Successfully removed the bot from **{guild.name}** (ID: {guild_id}).", ephemeral=False)
        else:
            await ctx.send(f"Could not find a server with ID: {guild_id}.", ephemeral=False)
    
    @slash_command(
        name='eval_basic_python_constants',
        description="See how python stores a constant, like `0xfF+0o42` would return `289`"
    )
    @slash_option("input_constant", description=r"a Python constant, like `'\u2603'` would return `'☃'`", opt_type=OptionType.STRING, required=True, max_length=45)
    async def eval_basic_python_constants(self, ctx: SlashContext, input_constant: str):
        if len(input_constant) > 45:
            return
        
        input_constant = input_constant.replace('\n','').replace('\r\n','')
        try:
            res = get_cool_thing(input_constant)
        except SyntaxError:
            await ctx.send(f'There was a SyntaxError with {input_constant}, youre doing something wrong')
            return
        except CouldNotEvalConstatCause2Large:
            await ctx.send(f'The expression you gave is too large, it was not compiled to a single constant')
            return
            
        await ctx.send(res)
