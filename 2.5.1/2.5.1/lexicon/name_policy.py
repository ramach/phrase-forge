"""Offline name classification. Frequency is never evidence of common meaning."""
from functools import lru_cache

# Editorial exceptions: ordinary English senses, not the named entity.
COMMON_SENSES = {
    'amazon': 'A tall or powerful woman (common noun).',
    'turkey': 'A large bird.', 
    'china': 'Porcelain.', 'java': 'Coffee (informal).',
    'john': 'A toilet (informal).', 'rose': 'A flower; past tense of rise.',
    'mark': 'A sign or indication.', 'grant': 'To give or authorize.',
    'hope': 'Expectation or desire.', 'bill': 'A statement of charges.',
    'will': 'Intention or determination.', 'grace': 'Elegance or kindness.',
    'faith': 'Trust or belief.', 'joy': 'Great pleasure.', 'amber': 'Fossil resin.',
    'violet': 'A flower or color.', 'hazel': 'A shrub or color.', 'olive': 'A fruit.',
    'ruby': 'A gemstone.', 'pearl': 'A gem formed in a mollusk.',
    'jasper': 'An opaque variety of quartz.', 'heather': 'A flowering shrub.',
    'holly': 'An evergreen shrub.', 'ivy': 'A climbing plant.', 'daisy': 'A flower.',
    'lily': 'A flower.', 'iris': 'A flower or part of the eye.', 'poppy': 'A flower.',
    'sage': 'A wise person or herb.', 'basil': 'An herb.', 'rosemary': 'An herb.',
    'summer': 'A season.', 'autumn': 'A season.', 'winter': 'A season.',
    'april': '', 'may': 'Expresses possibility.', 'march': 'To walk in step.',
    'august': 'Majestic or dignified.', 'chase': 'To pursue.', 'hunter': 'One who hunts.',
    'mason': 'A worker in stone.', 'carter': 'One who drives a cart.',
    'taylor': '', 'cooper': 'A maker of barrels.', 'porter': 'A carrier or dark beer.',
    'fletcher': 'A maker of arrows.', 'archer': 'One who shoots arrows.',
    'smith': 'A metalworker.', 'baker': 'One who bakes.', 'miller': 'One who mills grain.',
    'fisher': 'One who fishes.', 'walker': 'One who walks.', 'ranger': 'A person who patrols.',
    'tanner': 'One who tans hides.', 'turner': 'One who turns objects on a lathe.',
    'sawyer': 'One who saws wood.', 'singer': 'One who sings.', 'sailor': 'A seafarer.',
    'shelter': 'Protection or refuge.', 'harmony': 'Agreement or musical concord.',
    'melody': 'A sequence of musical notes.', 'destiny': 'Fate.', 'charity': 'Generosity.',
    'patience': 'Capacity to wait calmly.', 'prudence': 'Careful judgment.',
    'temperance': 'Moderation.', 'felicity': 'Happiness.', 'verity': 'Truth.',
    'justice': 'Fairness.', 'liberty': 'Freedom.', 'victory': 'Success in a contest.',
    'crystal': 'A solid with ordered structure.', 'diamond': 'A gemstone.',
    'sapphire': 'A gemstone.', 'emerald': 'A gemstone.', 'coral': 'Marine skeletal material.',
    'river': 'A natural watercourse.', 'brook': 'A small stream.', 'meadow': 'Grassland.',
    'forest': 'Woodland.', 'rain': 'Precipitation.', 'storm': 'Severe weather.',
    'sky': 'The atmosphere above.', 'dawn': 'Daybreak.', 'sunny': 'Bright with sunlight.',
    'ginger': 'A spice.', 'pepper': 'A spice.', 'cinnamon': 'A spice.',
    'angel': 'A spiritual being.', 'dove': 'A bird.', 'raven': 'A bird.',
    'robin': 'A bird.', 'wren': 'A bird.', 'phoenix': 'A mythical bird.',
    'mercury': 'A chemical element.', 'atlas': 'A collection of maps.',
    'titan': 'A person of exceptional importance.', 'herculean': 'Requiring great strength.',
    'adrian': '', 'already': 'Previously.', 'enraged': 'Very angry.',
    'abridge': 'To shorten.', 'arouse': 'To awaken or stimulate.',
    'amuser': 'One who amuses.', 'in flame': '', 'inf lame': '', 'inflame': 'To provoke or ignite.',
    'earnest': 'Serious and sincere.', 'sterling': 'Of excellent quality; British currency.',
    'frank': 'Candid.', 'cliff': 'A steep rock face.', 'clay': 'Fine-grained earth.',
    'reed': 'A tall grass.', 'rock': 'Stone.', 'stone': 'Rock.', 'flint': 'A hard stone.',
    'garnet': 'A gemstone.', 'opal': 'A gemstone.', 'onyx': 'A mineral.',
    'boston': '', 'reading': 'The act of reading.', 'bath': 'Washing or a container for washing.',
    'mobile': 'Able to move.', 'nice': 'Pleasant.', 'orange': 'A fruit or color.',
    'buffalo': 'A large bovine.', 'spring': 'A season or elastic device.',
    'sandy': 'Containing sand.', 'dusty': 'Covered in dust.', 'misty': 'Full of mist.',
    'brandy': 'A distilled spirit.', 'candy': 'A sweet confection.',
    'penny': 'A coin.', 'piper': 'A player of pipes.', 'page': 'A sheet of a book.',
    'lane': 'A narrow road.', 'gale': 'A strong wind.', 'guy': 'A person (informal).',
    'chuck': 'To throw.',  'jack': 'A lifting device.',
    'jill': '',  'art': 'Creative expression.',
    'pat': 'A light tap.', 'ray': 'A beam of light.', 'rod': 'A straight bar.',
    'rob': 'To steal from.', 'don': 'To put on.', 'bob': 'To move up and down.',
    'skip': 'To leap or omit.', 'chip': 'A small fragment.', 'bud': 'An immature shoot.',
    'gene': 'A unit of heredity.', 'norm': 'A standard.', 'rick': 'A stack of hay.',
    'lance': 'A spear.', 'wade': 'To walk through water.', 'pierce': 'To penetrate.',
    'shelley': '', 'darwin': '', 'hamlet': 'A small village.',
    'romeo': 'A romantic lover.', 'shylock': '', 'portia': '',
}
COMMON_SENSES = {k:v for k,v in COMMON_SENSES.items() if v and k.isalpha()}
# Known names not covered by the original first-name corpus. Single tokens only.
EXTRA_NAMES = frozenset('''shakespeare venice verona padua belmont shylock bassanio portia antonio jessica lorenzo gratiano nerissa salerio solanio tubal gobbo morocco aragon england scotland ireland wales france germany italy spain portugal europe africa america asia australia antarctica canada mexico brazil argentina california texas florida chicago boston seattle denver dallas houston london paris berlin madrid lisbon rome athens moscow beijing shanghai tokyo kyoto osaka mumbai delhi bengaluru bangalore chennai kolkata hyderabad singapore malaysia indonesia thailand vietnam cambodia pakistan bangladesh nepal bhutan afghanistan iran iraq israel palestine egypt nigeria kenya uganda tanzania ethiopia somalia sudan algeria tunisia libya ghana senegal angola zambia zimbabwe namibia botswana rwanda congo madagascar mauritius ukraine poland sweden norway finland denmark iceland austria belgium netherlands switzerland greece turkey russia china japan korea taiwan philippines mongolia siberia himalaya everest kilimanjaro sahara amazon nile ganges thames danube mississippi colorado sacramento francisco angeles diego york brooklyn manhattan queens harlem cambridge oxford stanford princeton harvard yale mit einstein newton darwin galileo aristotle socrates plato homer virgil dickens austen tolstoy dostoevsky sherlock holmes watson napoleon cleopatra caesar augustus alexander washington lincoln jefferson kennedy obama trump gandhi mandela mozart beethoven bach chopin picasso rembrandt michelangelo leonardo raphael hemingway twain orwell gandalf frodo hermione dumbledore hogwarts'''.split())

@lru_cache(maxsize=1)
def geographic_names():
    """Optional offline gazetteer; no network or API calls at runtime."""
    try:
        import geonamescache
        gc = geonamescache.GeonamesCache()
        return frozenset(x['name'].lower() for group in (gc.get_cities(), gc.get_countries(), gc.get_us_states()) for x in group.values() if x['name'].isascii() and x['name'].isalpha())
    except (ImportError, AttributeError, KeyError):
        return frozenset()

@lru_cache(maxsize=1)
def extra_names():
    return EXTRA_NAMES | geographic_names()
