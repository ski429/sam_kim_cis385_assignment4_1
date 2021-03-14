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
            abort(404, message="No note with that note_id.")
        return result

    @marshal_with(resource_fields)
    def put(self, note_id):
        args = notes_put_args.parse_args()
        result = NoteModel.query.filter_by(id=note_id).first()
        if not result:
            abort(404, message="No note with that note_id.")
        note = NoteModel(id=note_id, title=args['title'], body=args['body'])
        db.session.add(note)
        db.session.commit()
        return note, 201

    def delete(self, note_id):
        pass


class NoteByTitle(Resource):
    def get(self, title):
        pass

    def put(self, title):
        pass

    def post(self, title):
        pass


class AllNotes(Resource):
    def get(self):
        pass


api.add_resource(Note, '/notes/<int:note_id>')
api.add_resource(NoteByTitle, '/notes/<string:title>')
api.add_resource(AllNotes, '/notes/')

if __name__ == '__main__':
    app.run(debug=True)