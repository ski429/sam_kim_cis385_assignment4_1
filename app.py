from flask import Flask, request, jsonify, make_response
from flask_restful import Resource, Api, reqparse, fields, marshal_with, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
import traceback

app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    notes = db.relationship('Note', backref='author', lazy=True)


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20), nullable=False)
    body = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


# db.create_all()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Check for token in header
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        # Decode token, verify password, find user in database
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms="HS256")
            current_user = User.query.filter_by(id=data['id']).first()
        except:
            return jsonify({'message': 'Token is invalid!'})

        return f(current_user, *args, **kwargs)
    return decorated


notes_put_args = reqparse.RequestParser()
notes_put_args.add_argument("title", type=str, help="title of note")
notes_put_args.add_argument("body", type=str, help="body of note")

resource_fields = {
    'id': fields.Integer(default=None),
    'title': fields.String,
    'body': fields.String
}

user_fields = {
    'id': fields.Integer(default=None),
    'username': fields.String,
    'password': fields.String
}


class NoteById(Resource):
    @marshal_with(resource_fields)
    def get(self, note_id):
        result = Note.query.filter_by(id=note_id).first()
        if not result:
            abort(404, message="That note does not exist.")
        return result

    @marshal_with(resource_fields)
    def patch(self, note_id):
        args = notes_put_args.parse_args()
        result = Note.query.filter_by(id=note_id).first()
        if not result:
            abort(404, message="That note does not exist.")
        result.title = args['title']
        result.body = args['body']
        db.session.commit()
        return result, 201

    @marshal_with(resource_fields)
    def delete(self, note_id):
        result = Note.query.filter_by(id=note_id).first()
        if not result:
            abort(404, message="That note does not exist.")
        db.session.delete(result)
        db.session.commit()
        return 'Note {} deleted'.format(note_id), 200


class NoteByTitle(Resource):
    @marshal_with(resource_fields)
    def get(self, note_title):
        result = Note.query.filter_by(title=note_title).first()
        if not result:
            abort(404, message="That note does not exist.")
        return result

    @marshal_with(resource_fields)
    def patch(self, note_title):
        args = notes_put_args.parse_args()
        result = Note.query.filter_by(title=note_title).first()
        if not result:
            abort(404, message="That note does not exist.")
        result.body = args['body']
        db.session.commit()
        return result, 201

    @marshal_with(resource_fields)
    def post(self, note_title):
        args = notes_put_args.parse_args()
        result = Note.query.filter_by(title=note_title).first()
        if result:
            abort(404, message="A note with the same title exists")
        note = Note(title=note_title, body=args['body'])
        db.session.add(note)
        db.session.commit()
        return note, 200


class AllNotes(Resource):
    @marshal_with(resource_fields)
    def get(self):
        query = Note.query.all()
        return query


class UserById(Resource):
    @token_required
    @marshal_with(user_fields)
    def get(current_user, self, user_id):
        user = User.query.filter_by(id=user_id).first()
        if not user:
            abort(404, message="That user does not exist.")
        return user

    @token_required
    def delete(current_user, self, user_id):
        user = User.query.filter_by(id=user_id).first()
        if not user:
            abort(404, message="That user does not exist.")
        db.session.delete(user)
        db.session.commit()
        return make_response('User has been deleted.', 200)


class AllUsers(Resource):
    @token_required
    @marshal_with(user_fields)
    def get(current_user, self):
        query = User.query.all()
        return query

    @marshal_with(user_fields)
    def post(self):
        data = request.get_json()
        hashed_password = generate_password_hash(data['password'], method='sha256')
        new_user = User(username=data['username'], password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return new_user


@app.route('/login')
def login():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return make_response('Invalid login.', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})

    user = User.query.filter_by(username=auth.username).first()

    if not user:
        return make_response('Invalid login.', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})

    if check_password_hash(user.password, auth.password):
        token = jwt.encode({'id': user.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)},
                           app.config['SECRET_KEY'], algorithm="HS256")

        return jsonify({'token': token})
    return make_response('Invalid login.', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})


api.add_resource(UserById, '/user/<int:user_id>')
api.add_resource(AllUsers, '/user/')
api.add_resource(NoteById, '/note/<int:note_id>')
api.add_resource(NoteByTitle, '/note/<string:note_title>')
api.add_resource(AllNotes, '/note/')

if __name__ == '__main__':
    app.run(debug=True)