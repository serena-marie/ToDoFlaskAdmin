import os
from flask import Flask, url_for, redirect, render_template, request, abort
from flask_admin import Admin
from flask_sqlalchemy import SQLAlchemy
from flask_admin.contrib.sqla import ModelView
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required, current_user
from flask_admin import helpers as admin_helpers


# database path
proj_dir = os.path.dirname(os.path.abspath(__file__))
db_file = "sqlite:////{}".format(os.path.join(proj_dir, "todo.db"))

app = Flask(__name__)
# set optional bootswatch theme
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
app.config['SQLALCHEMY_DATABASE_URI'] = db_file
# This allows editing
app.config['SECRET_KEY'] = 'mysecret'
db = SQLAlchemy(app)


# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    todos = db.relationship('Todo', backref='user', lazy=True)

    def __repr__(self):
        return '<User %r>' % self.name


# Custom Model View
class UserView(ModelView):
    form_columns = ['name']


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200))
    complete = db.Column(db.Boolean)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Todo %r>' % self.id


# Create Admin
admin = Admin(app, name='ToDo', template_mode='bootstrap3')

# Add model views
admin.add_view(UserView(User, db.session))
admin.add_view(ModelView(Todo, db.session))


# routes
@app.route('/')
def index():
    # Adding Guest user if not already in table
    if User.query.filter_by(name="Guest").first() is None:
        guest_info = {'id': 1, 'name': 'Guest'}
        adduser = User(**guest_info)
        db.session.add(adduser)
        db.session.commit()

    # Display
    incomplete = Todo.query.filter_by(complete=False).all()
    complete = Todo.query.filter_by(complete=True).all()
    usr = User.query.order_by(User.id).all()
    return render_template('index.html', incomplete=incomplete, complete=complete, usr=usr)


@app.route('/add', methods=['POST'])
def add():
    # return '<h1>{}</h1>'.format(request.form['username'])
    # The way this is set up - need to explicitly update user_id
    # todo = Todo(text=request.form['todoitem'], complete=False, user_id=request.form['user.name'])
    todo = Todo(text=request.form['todoitem'], complete=False, user_id=request.form['username'])

    db.session.add(todo)
    db.session.commit()
    return redirect(url_for('index'))
#     # return '<h1>{}</h1>'.format(request.form['todoitem']) # now we know it was received


@app.route('/new', methods=['POST'])
def new_member():
    # return '<h1>{}</h1>'.format(request.form['newname'])
    newUser = User(name=request.form['newname'])
    db.session.add(newUser)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/update', methods=['POST'])
def update():
    if request.method == "POST":
        selected = request.form.get("itemTest")
        todo = Todo.query.filter_by(id=int(selected)).first()  # because expecting only 1 itemsho
        todo.complete = True
        db.session.commit()
    return redirect(url_for('index'))


@app.route('/remove', methods=['POST'])
def remove():
    selected = request.form.get("itemTest")
    todo = Todo.query.filter_by(id=int(selected)).first()
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
