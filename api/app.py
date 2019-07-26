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


@app.route('/api/coin/<token_id>')
def rainbowcoin(token_id):
    image_url = _compose_image(token_id)
    hex_code = _get_hex_from_token(token_id)
    red, green, blue = _get_rgb_from_token(token_id)

    attributes = []
    _add_attribute(attributes, 'red', red, token_id)
    _add_attribute(attributes, 'green', green, token_id)
    _add_attribute(attributes, 'blue', blue, token_id)
    _add_attribute(attributes, 'hex', hex_code, token_id)

    return jsonify({
        'name': f"RainbowCoin {hex_code}",
        'description': f"RGB ({red}, {blue}, {green})",
        'image': image_url,
        'external_url': f"https://rainbowco.in/coin/{token_id}",
        'attributes': attributes
    })


@app.route('/api/factory/<token_id>')
def factory(token_id):
    token_id = int(token_id)
    attributes = []
    _add_attribute(attributes, 'number_inside', [1], token_id)

    return jsonify({
        'name': "One RainbowCoin",
        'description': "When you purchase this option, you will receive one RainbowCoin!",
        'image': 'https://storage.googleapis.com/rainbowco.in/factory/random-coin.png',
        'external_url': 'https://rainbowco.in/factory/%s' % token_id,
        'attributes': attributes
    })


def _add_attribute(existing, attribute_name, value, token_id, display_type=None):
    trait = {
        'trait_type': attribute_name,
        'value': value
    }
    if display_type:
        trait['display_type'] = display_type
    existing.append(trait)


def _compose_image(token_id, path="coins"):
    red, green, blue = _get_rgb_from_token(token_id)
    luminance = _get_luminance_from_rgb(red, green, blue)

    bkg = Image.new('RGBA', (COIN_SIZE + COIN_PADDING,
                             COIN_SIZE + COIN_PADDING), (0, 0, 0, 0))
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
    tmp, blue = divmod(int(token_id), 256)
    tmp, green = divmod(tmp, 256)
    alpha, red = divmod(tmp, 256)
    return red, green, blue


def _get_hex_from_token(token_id):
    red, green, blue = _get_rgb_from_token(token_id)
    return "#{:02x}{:02x}{:02x}".format(red, green, blue).upper()


def _get_luminance_from_rgb(red, green, blue):
    return (.299 * red) + (.587 * green) + (.114 * blue)


if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
