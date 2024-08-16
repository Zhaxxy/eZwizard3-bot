from typing import Sequence
import re

from interactions import Extension, slash_command, SlashContext, slash_option, SlashCommandChoice, OptionType, AutocompleteContext, Embed
from rapidfuzz import fuzz, utils

from data_files import KNOWN_TITLE_IDS, KNOWN_REGIONS, REGION_EMOJIS

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
                print(found_things)
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
