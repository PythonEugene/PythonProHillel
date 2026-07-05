from flask import Blueprint, render_template, redirect, url_for, flash
from db_config import db
from db_utils import creat_task
from models import ToDoList
from forms import ToDoListForm


app = Blueprint("app", __name__)

@app.route('/')
def index():
    tasks = ToDoList.query.order_by(ToDoList.date).all()
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['GET', 'POST'])
def add_tasks():
    form = ToDoListForm()
    if form.validate_on_submit():
        new_task = ToDoList(
            title=form.title.data,
            description=form.description.data,
            date=form.date.data
        )
        creat_task(new_task)
        return redirect(url_for('app.index'))
    return render_template('add_task.html', form=form)

@app.route('/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    task = ToDoList.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted successfully!')
    return redirect(url_for('app.index'))


@app.route('/complete/<int:task_id>')
def complete_task(task_id):
    task = ToDoList.query.get_or_404(task_id)
    task.is_completed = True
    db.session.commit()
    flash('Task completed successfully!')
    return redirect(url_for('app.index'))




