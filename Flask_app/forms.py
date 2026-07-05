from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField
from wtforms.validators import DataRequired, length

class ToDoListForm(FlaskForm):
    title = StringField("Task", validators=[DataRequired(), length(max=99)])
    description = TextAreaField("Task description", validators=[length(max=500)])
    date = DateField("Deadline", format='%Y-%m-%d', validators=[DataRequired()])
