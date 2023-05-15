from flask_restful import Api, Resource, reqparse, inputs
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields
from flask.views import MethodView
from flask import Flask, abort
import datetime
import sys

app = Flask(__name__)
api = Api(app)
db = SQLAlchemy()
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///WebCalendar.db"
db.init_app(app)
parser = reqparse.RequestParser()
date_parser = reqparse.RequestParser()

parser.add_argument("event", type=str, help="The event name is required!", required=True, location='args')
parser.add_argument("date", type=inputs.date, help="The event date with the correct format is required! "
                                                   "The correct format is YYYY-MM-DD!", required=True, location='args')
date_parser.add_argument("start_time", type=inputs.date, help="The correct format is YYYY-MM-DD!", required=False,
                         location='args')
date_parser.add_argument("end_time", type=inputs.date, help="The correct format is YYYY-MM-DD!", required=False,
                         location='args')


class Calendar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.String, nullable=False)
    date = db.Column(db.Date, nullable=False)


with app.app_context():
    db.create_all()


class TaskSchema(Schema):
    id = fields.Integer()
    event = fields.String()
    date = fields.Date()


class WebCalendar(Resource):
    def get(self):
        args = date_parser.parse_args()
        schema = TaskSchema(many=True)
        if args["start_time"] is None:
            all_events = db.session.execute(db.select(Calendar)).scalars().all()
            return schema.dump(all_events)
        else:
            event_list = db.session.execute(db.select(Calendar).filter(
                Calendar.date.between(args["start_time"], args["end_time"]))).scalars().all()
            return schema.dump(event_list)


    def post(self):
        args = parser.parse_args()
        db.session.add(Calendar(event=args["event"], date=args["date"]))
        db.session.commit()
        args["date"] = str(args["date"].date())
        message = {"message": "The event has been added!"}
        message.update(args)
        return message


class EventById(Resource):
    def get(self, event_id):
        event = db.session.get(Calendar, event_id)
        if event is None:
            abort(404, "The event doesn't exist!")
        schema = TaskSchema()
        return schema.dump(event)

    def delete(self, event_id):
        event = db.session.get(Calendar, event_id)
        if event is None:
            abort(404, "The event doesn't exist!")
        db.session.delete(event)
        db.session.commit()
        return {"message": "The event has been deleted!"}


class TodayEvent(MethodView):
    def get(self):
        today_event = db.session.execute(db.select(Calendar).filter_by(date=datetime.date.today())).scalars().all()
        schema = TaskSchema(many=True)
        return schema.dump(today_event)


api.add_resource(WebCalendar, "/event")
api.add_resource(EventById, "/event/<int:event_id>")
app.add_url_rule('/event/today', view_func=TodayEvent.as_view('today_event'))

# do not change the way you run the program
if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()
