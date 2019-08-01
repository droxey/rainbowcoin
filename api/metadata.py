import json
import os
import string
import numpy as np
import pathlib
import requests
import webcolors

from google.cloud import storage
from google.oauth2 import service_account as sa
from PIL import Image, ImageDraw


COIN_SIZE = 500
STORAGE_CREDENTIALS = os.getenv('CREDENTIALS_FILE', 'credentials.json')
STORAGE_PROJECT = os.getenv('GOOGLE_STORAGE_PROJECT', 'RainbowCoin')
STORAGE_BUCKET = os.getenv('GOOGLE_STORAGE_BUCKET', 'rainbowco.in')
STORAGE_SCOPES = ['https://www.googleapis.com/auth/devstorage.read_write']
INTERNAL_ATTRIBUTES = ['red', 'green', 'blue', 'title', 'description', 'image']


def get_color_info(rgb_id):
    """Return everything we know about this rgb_id (an RGB integer)."""
    hex_code = _get_hex(rgb_id)
    hex_hash = title = f"#{hex_code}"
    red, green, blue = _get_rgb_from_token(rgb_id)
    title = hex_hash.upper()

    # Gather color stats and attributes.
    rgb_percent = webcolors.hex_to_rgb_percent(hex_hash)
    lum = _get_luminance(red, green, blue)

    # Normalize user-provided custom names for colors.
    title_is_hex = title.startswith('#')   # Implementation will change later
    if not title_is_hex:
        # We have a named color. Remove all punctuation from the string.
        title = title.translate(str.maketrans('', '', string.punctuation)).title()

    # Generate image assets and upload them to Google Storage Cloud.
    url = _compose_image(rgb_id, red, green, blue, lum)

    return {
        'title': title,
        'description': f'A {title} colored RainbowCoin.',
        'rgb_integer': int(rgb_id),
        'hex_code': hex_hash,
        'percentage_of_red': float(rgb_percent.red.replace('%', '')),
        'percentage_of_green': float(rgb_percent.green.replace('%', '')),
        'percentage_of_blue': float(rgb_percent.blue.replace('%', '')),
        'percentage_of_luminance': float("%.2f" % ((float(lum) / 255.0) * 100)),
        'rgb': f'({red}, {green}, {blue})',
        'image': url,
        'red': red,
        'green': green,
        'blue': blue,
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
        attr = {'trait_type': key, 'value': value}
        if isinstance(value, int) or isinstance(value, float):
            attr['display_type'] = 'number'
        # if key.startswith('percentage_of'):
        #     attr['display_type'] = 'boost_percent'
        attrs.append(attr)
    return attrs


def _compose_image(rgb_id, red, green, blue, lum, path="coins"):
    """Create a RainbowCoin, saved to images/output/{rgb_id}.png"""
    output_path = f"images/output/{rgb_id}.png"
    file = pathlib.Path(output_path)
    if file.exists():
        return f"https://storage.googleapis.com/rainbowco.in/coins/{rgb_id}.png"
    else:
        # Open the two high-res PNGs for the base and face.
        face =  Image.open('images/coin/coin-face.png').convert("RGBA")
        base = Image.open('images/coin/coin-base.png').convert("RGBA")

        # Generate a (height x width x 4) numpy array & unpack for readability.
        image_colors = np.array(face)
        r, g, b, a = image_colors.T

        # Replace all the lime green areas with the coin's minted color.
        green_areas = (r == 0) & (g == 255) & (b == 0)
        image_colors[..., :-1][green_areas.T] = (red, green, blue)

        # Create an ellipse from the numpy array and combine it with the base image.
        color_ellipse = Image.fromarray(image_colors)
        composite = Image.alpha_composite(base, color_ellipse)

        # Save the composite image to disk.
        composite.save(output_path)

        # Upload the composite to Google Storage.
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

def _get_rgb_from_token(rgb_id):
    tmp, blue= divmod(int(rgb_id), 256)
    tmp, green= divmod(tmp, 256)
    alpha, red= divmod(tmp, 256)
    return red, green, blue

def _get_hex(rgb_id):
    """Convert rgb_id (an RGB integer) to RGB, then return the corresponding hex code."""
    tmp, b = divmod(int(rgb_id), 256)
    tmp, g = divmod(tmp, 256)
    alpha, r = divmod(tmp, 256)
    return "{:02x}{:02x}{:02x}".format(r, g, b).upper()

def _get_luminance(r, g, b):
    """Returns the luminance value for a given RGB color."""
    return (.299 * r) + (.587 * g) + (.114 * b)
