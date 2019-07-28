import webcolors
import string

from colourlovers import clapi
from google.cloud import storage
from google.oauth2 import service_account
from PIL import Image, ImageDraw


GOOGLE_STORAGE_PROJECT = "RainbowCoin"
GOOGLE_STORAGE_BUCKET = "rainbowco.in"
COIN_BLACK = 'images/coin/coin.png'
COIN_WHITE = 'images/coin/coin-light.png'
COIN_PADDING = 3
COIN_SIZE = 500 - COIN_PADDING


def get_color_info(rgb_id):
    """Return everything we know about this rgb_id (an RGB integer)."""
    hex_code = _get_hex(rgb_id)
    hex_hash = title = f"#{hex_code}"

    # Call ColourLovers API and search for the hex color.
    cl = clapi.ColourLovers()
    clr = cl.search_color(hexvalue=hex_code, format='json')[0]

    # Gather color stats and attributes.
    rgb_percent = webcolors.hex_to_rgb_percent(hex_hash)
    lum = _get_luminance(clr.RGB.red, clr.RGB.blue, clr.RGB.green)

    # Normalize color title. Default is the hex code (with hash prefix).
    title_is_hex = clr.title.upper() == hex_code
    if not title_is_hex:
        # We have a named color. Remove all punctuation from the string.
        title = clr.title.translate(str.maketrans(
            '', '', string.punctuation)).title()

    # Generate image assets and upload them to Google Storage Cloud.
    url = _compose_image(rgb_id, clr.RGB.red,
                         clr.RGB.green, clr.RGB.blue, lum)

    return {
        'title': title,
        'description': f'A {title if title_is_hex else title.lower()} colored RainbowCoin.',
        'rgb_integer': int(rgb_id),
        'hex_code': hex_hash,
        'percentage_of_red': float(rgb_percent.red.replace('%', '')),
        'percentage_of_green': float(rgb_percent.green.replace('%', '')),
        'percentage_of_blue': float(rgb_percent.blue.replace('%', '')),
        'hsv': f'({clr.HSV.hue}, {clr.HSV.saturation}, {clr.HSV.value})',
        'rgb': f'({clr.RGB.red}, {clr.RGB.green}, {clr.RGB.blue})',
        'luminance': float("%.2f" % lum),
        'image': url,
        'red': clr.RGB.red,
        'green': clr.RGB.green,
        'blue': clr.RGB.blue,
    }


def get_color_attributes(info_dict):
    """Convert color information into OpenSea-compatible attributes."""
    attrs = []
    for key, value in info_dict.items():
        attr = {'trait_type': key, 'value': value, 'display_type': 'string'}
        if key == 'luminance':
            attr['display_type'] = 'boost_number'
        else:
            if isinstance(value, int) or isinstance(value, float):
                attr['display_type'] = 'number'
            if key.startswith('percentage_of'):
                attr['display_type'] = 'boost_percent'

        attrs.append(attr)
    return attrs


def _compose_image(rgb_id, red, green, blue, lum, path="coins"):
    """Create a RainbowCoin, saved to images/output/{rgb_id}.png"""
    bkg = Image.new('RGBA', (COIN_SIZE + COIN_PADDING,
                             COIN_SIZE + COIN_PADDING), (0, 0, 0, 0))

    draw = ImageDraw.Draw(bkg)
    draw.ellipse((COIN_PADDING, COIN_PADDING, COIN_SIZE, COIN_SIZE),
                 fill=(red, green, blue, 255))

    base_img = COIN_BLACK if lum > 30.0 else COIN_WHITE
    base = Image.open(base_img).convert("RGBA")
    output_path = "images/output/%s.png" % rgb_id
    composite = Image.alpha_composite(bkg, base)
    composite.save(output_path)

    blob = _get_bucket().blob(f"{path}/{rgb_id}.png")
    blob.upload_from_filename(filename=output_path)
    return blob.public_url


def _get_bucket():
    """Authenticates to the Google Storage Cloud bucket stored in credentials.json."""
    credentials = service_account.Credentials.from_service_account_file(
        'credentials.json')
    if credentials.requires_scopes:
        credentials = credentials.with_scopes(
            ['https://www.googleapis.com/auth/devstorage.read_write'])
    client = storage.Client(
        project=GOOGLE_STORAGE_PROJECT, credentials=credentials)
    return client.get_bucket(GOOGLE_STORAGE_BUCKET)


def _get_hex(rgb_id):
    """Convert rgb_id (an RGB integer) to RGB, then return the corresponding hex code."""
    tmp, b = divmod(int(rgb_id), 256)
    tmp, g = divmod(tmp, 256)
    alpha, r = divmod(tmp, 256)
    return "{:02x}{:02x}{:02x}".format(r, g, b).upper()


def _get_luminance(r, g, b):
    """Returns the luminance value for a given RGB color."""
    return (.299 * r) + (.587 * g) + (.114 * b)
