from flask import Flask
from db_config import db, DB_CONNECTION_STRING
from routes import app as app_routes


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dkfgnldk'
    app.config['SQLALCHEMY_DATABASE_URI'] = DB_CONNECTION_STRING
    db.init_app(app)
    app.register_blueprint(app_routes)

    with app.app_context():
        db.create_all()
    return app


if __name__== "__main__":
    app = create_app()
    app.run(debug=True)


