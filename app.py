from flask import Flask
from flask import request
from flask import jsonify

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/super_simple')
def super_simple():
    return jsonify(message='Hello from the Planetary API. '
                   'Planets are so much fun.')


@app.route('/not_found')
def not_found():
    return jsonify(message='That resource was not found'), 404


@app.route('/parameters')
def parameters():
    name = request.args.get('name')
    age = int(request.args.get('age'))

    if age < 18:
        return jsonify(message=f'Sorry {name}, you are not old enough.'), 401

    return jsonify(message=f'Welcome {name}, you are old enough.')


if __name__ == '__main__':
    app.run()
