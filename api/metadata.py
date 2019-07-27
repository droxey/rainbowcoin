
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


def get_color_attributes(token_id):
    """Return everything we know about this token_id (an RGB integer)."""
    hex_code = _get_hex(token_id)
    cl = clapi.ColourLovers()
    clr = cl.search_color(hexvalue=hex_code, format='json')[0]
    lum = _get_luminance(clr.RGB.red, clr.RGB.blue, clr.RGB.green)
    url = _compose_image(token_id, clr.RGB.red,
                         clr.RGB.green, clr.RGB.blue, lum)
    return {
        'name': clr.title.title(),
        'hex': clr.hex,
        'red': clr.RGB.red,
        'green': clr.RGB.green,
        'blue': clr.RGB.blue,
        'hue': clr.HSV.hue,
        'saturation': clr.HSV.saturation,
        'value': clr.HSV.value,
        'rank': clr.rank,
        'luminance': lum,
        'image': url
    }


def _compose_image(token_id, red, green, blue, lum, path="coins"):
    """Create a RainbowCoin, saved to images/output/{token_id}.png"""
    bkg = Image.new('RGBA', (COIN_SIZE + COIN_PADDING,
                             COIN_SIZE + COIN_PADDING), (0, 0, 0, 0))

    draw = ImageDraw.Draw(bkg)
    draw.ellipse((COIN_PADDING, COIN_PADDING, COIN_SIZE, COIN_SIZE),
                 fill=(red, green, blue, 255))

    base_img = COIN_BLACK if lum > 30.0 else COIN_WHITE
    base = Image.open(base_img).convert("RGBA")
    output_path = "images/output/%s.png" % token_id
    composite = Image.alpha_composite(bkg, base)
    composite.save(output_path)

    blob = _get_bucket().blob(f"{path}/{token_id}.png")
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


def _get_hex(token_id):
    """Convert token_id (an RGB integer) to RGB, then return the corresponding hex code."""
    tmp, b = divmod(int(token_id), 256)
    tmp, g = divmod(tmp, 256)
    alpha, r = divmod(tmp, 256)
    return "{:02x}{:02x}{:02x}".format(r, g, b).upper()


def _get_luminance(r, g, b):
    """Returns the luminance value for a given RGB color."""
    return (.299 * r) + (.587 * g) + (.114 * b)
