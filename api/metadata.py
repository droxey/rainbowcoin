import os
import webcolors
import string
import requests
import json

from colourlovers import clapi
from google.cloud import storage
from google.oauth2 import service_account as sa
from PIL import Image, ImageDraw


STORAGE_CREDENTIALS = os.getenv('CREDENTIALS_FILE', 'credentials.json')
STORAGE_PROJECT = os.getenv('GOOGLE_STORAGE_PROJECT', 'RainbowCoin')
STORAGE_BUCKET = os.getenv('GOOGLE_STORAGE_BUCKET', 'rainbowco.in')
STORAGE_SCOPES = ['https://www.googleapis.com/auth/devstorage.read_write']

COIN_BLACK = 'images/coin/coin.png'
COIN_WHITE = 'images/coin/coin-light.png'
COIN_PADDING = 3
COIN_SIZE = 500 - COIN_PADDING
INTERNAL_ATTRIBUTES = ['red', 'green', 'blue', 'title', 'description', 'image']


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
    # Try the color.pizza API first (largest named list).
    color_api = requests.get(f'https://api.color.pizza/v1/{hex_code}')
    resp = json.loads(color_api.text)
    try:
        color = resp['colors'][0]
        if color['distance'] <= 3:
            title = color['name']
    except KeyError:
        pass  # Not important enough to hold us up.

    title_is_hex = title.upper() == hex_code
    if title_is_hex:
        # If we didn't find a name from pizza.color,
        # Use the one we found with the CL API.
        title = clr.title
        title_is_hex = False

    if title_is_hex:
        title = hex_hash.upper()
    else:
        # We have a named color. Remove all punctuation from the string.
        title = title.translate(str.maketrans(
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
        'percentage_of_luminance': float("%.2f" % ((float(lum) / 255.0) * 100)),
        'hsv': f'({clr.HSV.hue}, {clr.HSV.saturation}, {clr.HSV.value})',
        'rgb': f'({clr.RGB.red}, {clr.RGB.green}, {clr.RGB.blue})',
        'image': url,
        'red': clr.RGB.red,
        'green': clr.RGB.green,
        'blue': clr.RGB.blue,
    }


def get_color_attributes(info_dict):
    """Convert color information into OpenSea-compatible attributes."""

    # Remove internal-only attributes before returning public metadata.
    external_attrs = info_dict.copy()
    for attr in INTERNAL_ATTRIBUTES:
        del(external_attrs[attr])

    # Generate attributes about this color.
    attrs = []
    for key, value in external_attrs.items():
        attr = {'trait_type': key, 'value': value, 'display_type': 'string'}
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
    credentials = sa.Credentials.from_service_account_file(STORAGE_CREDENTIALS)
    if credentials.requires_scopes:
        credentials = credentials.with_scopes(STORAGE_SCOPES)
    client = storage.Client(project=STORAGE_PROJECT, credentials=credentials)
    return client.get_bucket(STORAGE_BUCKET)


def _get_hex(rgb_id):
    """Convert rgb_id (an RGB integer) to RGB, then return the corresponding hex code."""
    tmp, b = divmod(int(rgb_id), 256)
    tmp, g = divmod(tmp, 256)
    alpha, r = divmod(tmp, 256)
    return "{:02x}{:02x}{:02x}".format(r, g, b).upper()


def _get_luminance(r, g, b):
    """Returns the luminance value for a given RGB color."""
    return (.299 * r) + (.587 * g) + (.114 * b)