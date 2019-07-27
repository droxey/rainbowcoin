from flask import Flask, jsonify
from metadata import get_color_attributes


app = Flask(__name__)


@app.route('/api/coin/<token_id>')
def rainbowcoin(token_id):
    info = get_color_attributes(token_id)

    return jsonify({
        'name': info['name'],
        'description': f"A {info['name'].lower()} colored RainbowCoin.",
        'image': info['image'],
        'external_url': f"https://rainbowco.in/coin/{token_id}",
        'attributes': info
    })


@app.route('/api/factory/<token_id>')
def factory(token_id):
    token_id = int(token_id)
    return jsonify({
        'name': "One RainbowCoin",
        'description': "When you purchase this option, you will receive one RainbowCoin!",
        'image': 'https://storage.googleapis.com/rainbowco.in/factory/random-coin.png',
        'external_url': 'https://rainbowco.in/factory/%s' % token_id,
        'attributes': []
    })


if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
