from flask import Flask, make_response
from flask_restful import Resource, Api, reqparse, fields, marshal_with
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
db.create_all()


class NoteModel(db.Model):
    id = db.Column(db.Integer, priamry_key=True)
    title = db.Column(db.String(20), nullable=False)
    body = db.Column(db.String(100), nullable=False)


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
        result = NoteModel.query.get(id=note_id)
        return result

    def put(self, note_id):
        temp = get_note("id", note_id)
        if temp is None:
            return make_response('Note {:d} not found.'.format(note_id), 404)
        args = notes_put_args.parse_args()
        print(args.items())
        for k, v in args.items():
            temp[k] = v
        return make_response(temp, 200)

    def delete(self, note_id):
        temp = get_note("id", note_id)
        if temp is None:
            return make_response('Note {:d} not found.'.format(note_id), 404)
        notes.remove(temp)
        return make_response('Note {:d} was deleted.'.format(note_id), 200)


class NoteByTitle(Resource):
    def get(self, title):
        temp = get_note("title", title)
        if temp is None:
            return make_response("Note not found.", 404)
        return make_response(temp, 200)

    def put(self, title):
        temp = get_note("title", title)
        if temp is None:
            return make_response("Note not found.", 404)
        args = notes_put_args.parse_args()
        temp["body"] = args["body"]
        return make_response(temp, 200)

    def post(self, title):
        if get_note("title", title) is not None:
            return make_response("Note already exists", 409)
        args = notes_put_args.parse_args()
        next_id = notes[-1]["id"] + 1
        args["id"] = next_id
        args["title"] = title
        notes.append(args)
        return make_response('New note with id: {:d} created.'.format(next_id), 200)


class AllNotes(Resource):
    def get(self):
        return notes


api.add_resource(Note, '/notes/<int:note_id>')
api.add_resource(NoteByTitle, '/notes/<string:title>')
api.add_resource(AllNotes, '/notes/')

if __name__ == '__main__':
    app.run(debug=True)