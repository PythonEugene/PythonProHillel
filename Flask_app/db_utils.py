from flask import flash
from db_config import db


def creat_task(task):
    if task:
        db.session.add(task)
        db.session.commit()
        flash("Task added", "succes")
