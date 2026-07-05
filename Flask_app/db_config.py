from flask import Flask
from flask_sqlalchemy import SQLAlchemy


DB_CONNECTION_STRING = "sqlite:///to_do_list.db"


db = SQLAlchemy()
