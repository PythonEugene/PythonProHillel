from db_config import db


class ToDoList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.Date, nullable=False)
    is_completed = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<ToDoList {self.title}>"





