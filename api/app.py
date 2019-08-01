import os
import exceptions
import metadata
import sentry_sdk

from flask import Flask, jsonify
from sentry_sdk.integrations.flask import FlaskIntegration

from dotenv import load_dotenv
load_dotenv()


sentry_sdk.init(dsn=os.getenv('SENTRY_DSN'), integrations=[FlaskIntegration()])
app = Flask(__name__)


@app.route('/coin/<rgb_id>')
def rainbowcoin(rgb_id):
    """Returns JSON-serialized ERC-721 metadata for a single RainbowCoin."""

    # Validate that rgb_id is a valid RGB integer.
    if int(rgb_id) not in range(0, 16777216):
        raise exceptions.InvalidUsage(
            f'{rgb_id} is not a valid RGB integer. Valid RGB integers range between 0 and 16,777,215.',
            status_code=500)

    # Get all the data for this RainbowCoin.
    info = metadata.get_color_info(rgb_id)
    attrs = metadata.get_color_attributes(info)

    # Render OpenSea-compatible JSON metadata.
    # See https://docs.opensea.io/docs/2-adding-metadata for more.
    return jsonify({
        'background_color': 'FFFFFF',
        'description': info['description'],
        'external_url': f"https://rainbowco.in/coin/{rgb_id}",
        'name': info['title'],
        'image': info['image'],
        'attributes': attrs,
    })


@app.errorhandler(exceptions.InvalidUsage)
def handle_invalid_usage(error):
    """Handles exceptions and returns a helpful error to the user."""
    response = jsonify({'error': error.to_dict().get('message')})
    response.status_code = error.status_code
    return response


# @app.route('/api/factory/<rgb_id>')
# def factory(rgb_id):
#     rgb_id = int(rgb_id)
#     return jsonify({
#         'name': "One RainbowCoin",
#         'description': "When you purchase this option, you will receive one RainbowCoin!",
#         'image': 'https://storage.googleapis.com/rainbowco.in/factory/random-coin.png',
#         'external_url': 'https://rainbowco.in/factory/%s' % rgb_id,
#         'attributes': []
#     })


if __name__ == '__main__':
    app.run(
        debug=os.getenv('DEBUG', True),
        use_reloader=True)
