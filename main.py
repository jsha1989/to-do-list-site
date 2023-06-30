from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, SubmitField
from wtforms.validators import InputRequired, Length
from datetime import date, datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = "secret"

db = SQLAlchemy()
bootstrap = Bootstrap(app)

# configure database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///to-do-list.db"
db.init_app(app)

class Tasks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String, unique=False, nullable=False)
    info = db.Column(db.String, unique=False, nullable=True)
    tags = db.Column(db.String, unique=False, nullable=True)
    due_date = db.Column(db.Date, unique=False, nullable=True)
    priority = db.Column(db.String, unique=False, nullable=True)
    status = db.Column(db.String, unique=False, nullable=False)
    complete_date = db.Column(db.Date, unique=False, nullable=True)

# with app.app_context():
#     db.create_all()
#
#     test_task = Tasks(
#         task="finish this site",
#         info="Assignment to make a to-do list website",
#         tags="Python, Web design",
#         due_date=datetime(2023, 6, 30),
#         priority="1 (High)",
#         status="In Progress",
#     )
#     db.session.add(test_task)
#     db.session.commit()

# form to add new task
class AddTask(FlaskForm):
    new_task_name = StringField('Task', validators=[InputRequired(), Length(max=70)])
    new_task_info = StringField('Add extra info (optional)', validators=[Length(max=120)])
    new_task_tags = StringField('Add associated tags (optional)', validators=[Length(max=50)])
    new_task_due = DateField('Due Date')
    new_task_priority = SelectField('Priority', choices=['1 (High)','2 (Normal)','3 (Low)'])
    new_task_status = SelectField('Status', choices=['Not Started','In Progress','Complete'])
    submit = SubmitField('Submit')

# return to previous page
def redirect_url(default='index'):
    return request.referrer or \
            url_for(default)

# show current tasks (home page)
@app.route("/")
def index():
    all_tasks = Tasks.query.filter(Tasks.status !="Complete").all()
    return render_template("index.html", tasks=all_tasks)

@app.route("/sort-priority")
def sort_priority():
    priority_tasks = Tasks.query.filter(Tasks.status !="Complete").order_by(Tasks.priority).all()
    return render_template("index.html", tasks=priority_tasks)

@app.route("/sort-date")
def sort_date():
    date_tasks = Tasks.query.filter(Tasks.status !="Complete").order_by(Tasks.due_date).all()
    return render_template("index.html", tasks=date_tasks)

# show completed tasks
@app.route("/completed")
def show_completed():
    completed_tasks = Tasks.query.filter_by(status="Complete").all()
    return render_template("completed.html", tasks=completed_tasks)

# search tasks by tag
@app.route("/search/")
def search():
    search_tag = request.args['search']
    searched_tasks = Tasks.query.filter(Tasks.tags.contains(search_tag))
    return render_template("search-result.html", tasks=searched_tasks, search_tag=search_tag)

# add new task
@app.route("/add", methods=["GET", "POST"])
def add_task():
    new_task_form = AddTask()
    if new_task_form.validate_on_submit():
        # format date into date obj
        y,m,d = request.form['new_task_due'].split('-')
        formatted_date = datetime(int(y), int(m), int(d))
        # add new task to db
        new_task = Tasks(
            task=request.form['new_task_name'],
            info=request.form['new_task_info'],
            tags=request.form['new_task_tags'],
            due_date=formatted_date,
            priority=request.form['new_task_priority'],
            status=request.form['new_task_status']
        )
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add.html', form=new_task_form)

# update task
@app.route("/edit-task/<task_id>", methods=["GET", "POST", "PATCH"])
def edit_task(task_id):
    task_to_edit = Tasks.query.get(task_id)
    edit_form = AddTask(
        new_task_name=task_to_edit.task,
        new_task_info=task_to_edit.info,
        new_task_tags=task_to_edit.tags,
        new_task_due=task_to_edit.due_date,
        new_task_priority=task_to_edit.priority,
        new_task_status=task_to_edit.status,
    )
    if edit_form.validate_on_submit():
        # format date into date obj
        y, m, d = request.form['new_task_due'].split('-')
        formatted_date = datetime(int(y), int(m), int(d))
        # update db
        task_to_edit.task = request.form['new_task_name']
        task_to_edit.info = request.form['new_task_info']
        task_to_edit.tags = request.form['new_task_tags']
        task_to_edit.due_date = formatted_date
        task_to_edit.priority = request.form['new_task_priority']
        task_to_edit.status = request.form['new_task_status']
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('edit.html', form=edit_form)

# delete task
@app.route("/delete-task/<task_id>", methods=["GET", "DELETE"])
def delete_task(task_id):
    task_to_delete = Tasks.query.get(task_id)
    db.session.delete(task_to_delete)
    db.session.commit()
    return redirect(redirect_url())

# shortcut to mark task as done
@app.route("/mark_done/<task_id>", methods=["GET", "PATCH"])
def mark_done(task_id):
    task_to_edit = Tasks.query.get(task_id)
    task_to_edit.status = "Complete"
    task_to_edit.complete_date = date.today()
    db.session.commit()
    return redirect(redirect_url())

if __name__ == '__main__':
    app.run(debug=True)