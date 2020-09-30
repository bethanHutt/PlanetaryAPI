import os

from flask import Flask
from flask import request
from flask import jsonify

from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import Float
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer

from flask_marshmallow import Marshmallow

from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required
from flask_jwt_extended import create_access_token

from flask_mail import Mail
from flask_mail import Message

base_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(
    base_dir, 'planets.db')

app.config['JWT_SECRET_KEY'] = os.environ['JWT_SECRET_KEY']
app.config['MAIL_SERVER'] = os.environ['MAIL_SERVER']
app.config['MAIL_USERNAME'] = os.environ['MAIL_USERNAME']
app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']

db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)
mail = Mail(app)


@app.cli.command('db_create')
def db_create():
    db.create_all()
    print('Database created.')


@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print('Database dropped.')


@app.cli.command('db_seed')
def db_seed():
    mercury = Planet(
        planet_name='Mercury',
        planet_type='Class D',
        home_star='Sol',
        mass=3.258e23,
        radius=1516,
        distance=35.98e6)

    venus = Planet(
        planet_name='Venus',
        planet_type='Class K',
        home_star='Sol',
        mass=4.867e24,
        radius=3760,
        distance=67.24e6)

    earth = Planet(
        planet_name='Earth',
        planet_type='Class M',
        home_star='Sol',
        mass=5.972e24,
        radius=3959,
        distance=92.96e6)

    db.session.add(mercury)
    db.session.add(venus)
    db.session.add(earth)

    test_user = User(
        first_name='William',
        last_name='Herschel',
        email='test@test.com',
        password='password')

    db.session.add(test_user)
    db.session.commit()
    print('Database seeded.')


# API Endpoints


@ app.route('/')
def hello_world():
    return 'Hello World!'


@ app.route('/super_simple')
def super_simple():
    return jsonify(message='Hello from the Planetary API. '
                   'Planets are so much fun.')


@ app.route('/not_found')
def not_found():
    return jsonify(message='That resource was not found'), 404


@ app.route('/parameters')
def parameters():
    name = request.args.get('name')
    age = int(request.args.get('age'))

    if age < 18:
        return jsonify(message=f'Sorry {name}, you are not old enough.'), 401

    return jsonify(message=f'Welcome {name}, you are old enough.')


@ app.route('/url_variables/<string:name>/<int:age>')
def url_variables(name: str, age: int):
    print('here')
    if age < 18:
        return jsonify(message=f'Sorry {name}, you are not old enough.'), 401

    return jsonify(message=f'Welcome {name}, you are old enough.')


@app.route('/planets', methods=['GET'])
def planets():
    planets_list = Planet.query.all()
    result = planets_schema.dump(planets_list)

    return jsonify(result)


@app.route('/planet_details/<int:planet_id>', methods=['GET'])
def planet_details(planet_id: int):
    planet = Planet.query.filter_by(planet_id=planet_id).first()

    if not planet:
        return jsonify(message='That planet does not exist.'), 404

    result = planet_schema.dump(planet)
    return jsonify(result)


@app.route('/add_planet', methods=['POST'])
@jwt_required
def add_planet():
    planet_name = request.form['planet_name']

    preexisting_planet = Planet.query.filter_by(
        planet_name=planet_name).first()

    if preexisting_planet:
        return jsonify(message='There is already a planet by that name'), 409

    planet_type = request.form['planet_type']
    home_star = request.form['home_star']
    mass = float(request.form['mass'])
    radius = float(request.form['radius'])
    distance = float(request.form['distance'])

    new_planet = Planet(planet_name=planet_name, planet_type=planet_type,
                        home_star=home_star, mass=mass,
                        radius=radius, distance=distance)

    db.session.add(new_planet)
    db.session.commit()

    return jsonify(message='You added a planet!'), 201


@app.route('/update_planet', methods=['PUT'])
@jwt_required
def update_planet():
    planet_id = int(request.form['planet_id'])

    planet = Planet.query.filter_by(
        planet_id=planet_id).first()

    if not planet:
        return jsonify(message='That planet does not exist'), 404

    planet.planet_name = request.form['planet_name']
    planet.planet_type = request.form['planet_type']
    planet.home_star = request.form['home_star']
    planet.distance = float(request.form['distance'])
    planet.mass = float(request.form['mass'])
    planet.radius = float(request.form['radius'])

    db.session.commit()
    return jsonify(message='You updated a planet'), 202


@app.route('/remove_planet/<int:planet_id>', methods=['DELETE'])
@jwt_required
def remove_planet(planet_id: int):
    planet = Planet.query.filter_by(
        planet_id=planet_id).first()

    if not planet:
        return jsonify(message='That planet does not exist'), 404

    db.session.delete(planet)
    db.session.commit()
    return jsonify(message='You deleted a planet.'), 202


@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    preexisting_user = User.query.filter_by(email=email).first()

    if preexisting_user:
        return jsonify(message='That email already exists.'), 409

    first_name = request.form['first_name']
    last_name = request.form['last_name']
    password = request.form['password']

    user = User(first_name=first_name, last_name=last_name,
                email=email, password=password)

    db.session.add(user)
    db.session.commit()

    return jsonify(message='User created successfully.'), 201


@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        email = request.json['email']
        password = request.json['password']
    else:
        email = request.form['email']
        password = request.form['password']

    test = User.query.filter_by(email=email, password=password).first()
    if test:
        access_token = create_access_token(identity=email)
        return jsonify(message='Login succeeded!', access_token=access_token)

    return jsonify(message='Bad email or password.'), 401


@app.route('/retrieve_password/<string:email>', methods=['GET'])
def retrieve_password(email: str):
    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify(message='That email doesn\'t exist.'), 401

    msg = Message(f'Your Planetary API password is: {user.password}',
                  sender='admin@planetary-api.com',
                  recipients=[email])

    mail.send(msg)

    return jsonify(message=f'Password sent to {email}')

# Database Models


class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)


class Planet(db.Model):
    __tablename__ = 'planets'
    planet_id = Column(Integer, primary_key=True)
    planet_name = Column(String)
    planet_type = Column(String)
    home_star = Column(String)
    mass = Column(Float)
    radius = Column(Float)
    distance = Column(Float)


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email', 'password')


user_schema = UserSchema()
users_schema = UserSchema(many=True)


class PlanetSchema(ma.Schema):
    class Meta:
        fields = ('planet_id', 'planet_name', 'planet_type', 'home_star',
                  'mass', 'radius', 'distance')


planet_schema = PlanetSchema()
planets_schema = PlanetSchema(many=True)


if __name__ == '__main__':
    app.run()
