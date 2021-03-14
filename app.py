from flask import Flask
from flask_restful import Resource, Api, reqparse, fields, marshal_with, abort
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)


class NoteModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20), nullable=False)
    body = db.Column(db.String(100), nullable=False)


db.create_all()

notes_put_args = reqparse.RequestParser()
notes_put_args.add_argument("title", type=str, help="title of note")
notes_put_args.add_argument("body", type=str, help="body of note")

resource_fields = {
    'id': fields.Integer,
    'title': fields.String,
    'body': fields.String
}


class Note(Resource):
    @marshal_with(resource_fields)
    def get(self, note_id):
        result = NoteModel.query.filter_by(id=note_id).first()
        if not result:
            abort(404, message="That note does not exist.")
        return result

    @marshal_with(resource_fields)
    def patch(self, note_id):
        args = notes_put_args.parse_args()
        result = NoteModel.query.filter_by(id=note_id).first()
        if not result:
            abort(404, message="That note does not exist.")
        note = NoteModel(id=note_id, title=args['title'], body=args['body'])
        db.session.add(note)
        db.session.commit()
        return note, 201

    @marshal_with(resource_fields)
    def delete(self, note_id):
        result = NoteModel.query.filter_by(id=note_id).first()
        if not result:
            abort(404, message="That note does not exist.")
        db.session.delete(result)
        db.session.commit()
        return 'Note {} deleted'.format(note_id), 200


class NoteByTitle(Resource):
    def get(self, note_title):
        pass

    def patch(self, note_title):
        pass

    @marshal_with(resource_fields)
    def post(self, note_title):
        args = notes_put_args.parse_args()
        result = NoteModel.query.filter_by(title=note_title).first()
        if result:
            abort(404, message="A note with the same title exists")
        note = NoteModel(title=note_title, body=args['body'])
        db.session.add(note)
        db.session.commit()
        return note, 200


class AllNotes(Resource):
    def get(self):
        pass


api.add_resource(Note, '/notes/<int:note_id>')
api.add_resource(NoteByTitle, '/notes/<string:note_title>')
api.add_resource(AllNotes, '/notes/')

if __name__ == '__main__':
    app.run(debug=True)