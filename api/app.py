import os
import mimetypes

from flask import Flask
from flask import jsonify

from google.cloud import storage
from google.oauth2 import service_account
from PIL import Image, ImageDraw


COIN_BLACK = 'images/coin/coin.png'
COIN_WHITE = 'images/coin/coin-light.png'
GOOGLE_STORAGE_PROJECT = "RainbowCoin"
GOOGLE_STORAGE_BUCKET = "rainbowco.in"
COIN_PADDING = 3
COIN_SIZE = 500 - COIN_PADDING

app = Flask(__name__)


# FIRST_NAMES = ['Herbie', 'Sprinkles', 'Boris', 'Dave', 'Randy', 'Captain']
# LAST_NAMES = ['Starbelly', 'Fisherton', 'McCoy']
# BASES = ['jellyfish', 'starfish', 'crab', 'narwhal', 'tealfish', 'goldfish']
# EYES = ['big', 'joy', 'wink', 'sleepy', 'content']
# MOUTH = ['happy', 'surprised', 'pleased', 'cute']
# INT_ATTRIBUTES = [5, 2, 3, 4, 8]
# FLOAT_ATTRIBUTES = [1.4, 2.3, 11.7, 90.2, 1.2]
# STR_ATTRIBUTES = ['happy', 'sad', 'sleepy', 'boring']
# BOOST_ATTRIBUTES = [10, 40, 30]
# PERCENT_BOOST_ATTRIBUTES = [5, 10, 15]
# NUMBER_ATTRIBUTES = [1, 2, 1, 1]


@app.route('/api/coin/<token_id>')
def rainbowcoin(token_id):
    token_id = int(token_id)
    image_url = _compose_image(token_id)

    # base = BASES[token_id % len(BASES)]
    # eyes = EYES[token_id % len(EYES)]
    # mouth = MOUTH[token_id % len(MOUTH)]
    # attributes = []
    # _add_attribute(attributes, 'base', BASES, token_id)
    # _add_attribute(attributes, 'eyes', EYES, token_id)
    # _add_attribute(attributes, 'mouth', MOUTH, token_id)
    # _add_attribute(attributes, 'level', INT_ATTRIBUTES, token_id)
    # _add_attribute(attributes, 'stamina', FLOAT_ATTRIBUTES, token_id)
    # _add_attribute(attributes, 'personality', STR_ATTRIBUTES, token_id)
    # _add_attribute(attributes, 'aqua_power', BOOST_ATTRIBUTES,
    #                token_id, display_type="boost_number")
    # _add_attribute(attributes, 'stamina_increase', PERCENT_BOOST_ATTRIBUTES,
    #                token_id, display_type="boost_percentage")
    # _add_attribute(attributes, 'generation', NUMBER_ATTRIBUTES,
    #                token_id, display_type="number")

    return jsonify({
        'name': "RainbowCoin %s" % _get_hex_from_token(token_id),
        'description': "TODO: Description for a single RainbowCoin",
        'image': image_url,
        'external_url': 'https://rainbowco.in/coin/%s' % token_id,
        'attributes': [

        ]
    })


@app.route('/api/factory/<token_id>')
def factory(token_id):
    token_id = int(token_id)
    name = "One OpenSea creature"
    description = "When you purchase this option, you will receive a single OpenSea creature of a random variety. " \
                  "Enjoy and take good care of your aquatic being!"
    image_url = _compose_image(['images/factory/egg.png'], token_id, "factory")
    num_inside = 1
    attributes = []
    _add_attribute(attributes, 'number_inside', [num_inside], token_id)

    return jsonify({
        'name': name,
        'description': description,
        'image': image_url,
        'external_url': 'https://openseacreatures.io/%s' % token_id,
        'attributes': attributes
    })


def _add_attribute(existing, attribute_name, options, token_id, display_type=None):
    trait = {
        'trait_type': attribute_name,
        'value': options[token_id % len(options)]
    }
    if display_type:
        trait['display_type'] = display_type
    existing.append(trait)


def _compose_image(token_id, path="coins"):
    red, green, blue = _get_rgb_from_token(token_id)
    luminance = _get_luminance_from_rgb(red, green, blue)
    print(luminance)

    bkg = Image.new('RGBA', (COIN_SIZE + COIN_PADDING, COIN_SIZE + COIN_PADDING), (0, 0, 0, 0))
    draw = ImageDraw.Draw(bkg)
    draw.ellipse((COIN_PADDING, COIN_PADDING, COIN_SIZE, COIN_SIZE),
                  fill=(red, green, blue, 255))
    base_img = COIN_BLACK if luminance > 30.0 else COIN_WHITE
    base = Image.open(base_img).convert("RGBA")
    output_path = "images/output/%s.png" % token_id
    composite = Image.alpha_composite(bkg, base)
    composite.save(output_path)

    blob = _get_bucket().blob(f"{path}/{token_id}.png")
    blob.upload_from_filename(filename=output_path)
    return blob.public_url


def _get_bucket():
    credentials = service_account.Credentials.from_service_account_file(
        'credentials.json')
    if credentials.requires_scopes:
        credentials = credentials.with_scopes(
            ['https://www.googleapis.com/auth/devstorage.read_write'])
    client = storage.Client(
        project=GOOGLE_STORAGE_PROJECT, credentials=credentials)
    return client.get_bucket(GOOGLE_STORAGE_BUCKET)


def _get_rgb_from_token(token_id):
    tmp, blue= divmod(int(token_id), 256)
    tmp, green= divmod(tmp, 256)
    alpha, red= divmod(tmp, 256)
    return red, green, blue

def _get_hex_from_token(token_id):
  red, green, blue = _get_rgb_from_token(token_id)
  return "#{:02x}{:02x}{:02x}".format(red, green, blue)

def _get_luminance_from_rgb(red, green, blue):
    return (.299 * red) + (.587 * green) + (.114 * blue)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
