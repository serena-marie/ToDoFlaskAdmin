import os

from flask import Flask, url_for, redirect, render_template, request, abort
from flask_admin import Admin, BaseView, expose, helpers as admin_helpers
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink
from flask_admin.form import SecureForm
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_login import LoginManager
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required, current_user
from flask_security.forms import LoginForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired
from datetime import datetime


############### Config ###############
# database path
proj_dir = os.path.dirname(os.path.abspath(__file__))
db_file = "sqlite:////{}".format(os.path.join(proj_dir, "todo.db"))

# create app
app = Flask(__name__)
login = LoginManager(app)

app.config['FLASK_ADMIN_SWATCH'] = 'journal'
app.config['SQLALCHEMY_DATABASE_URI'] = db_file
app.config['SECRET_KEY'] = 'mysecret'  # This allows editing & flask-login
app.config['SECURITY_PASSWORD_HASH'] = 'bcrypt'
app.config['SECURITY_PASSWORD_SALT'] = 'scoupon-secret'
app.config['DEBUG'] = True
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False # Don't send register email
app.config['SECURITY_POST_LOGIN_VIEW'] = '/admin'

# create db connection obj
db = SQLAlchemy(app)


############### Tables ###############
# Models
roles_users = db.Table('roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)
    description = db.Column(db.String(255))
    # user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    email = db.Column(db.String(50))
    password = db.Column(db.String(50))
    active = db.Column(db.Boolean())

    # relationships
    todos = db.relationship('Todo', backref='user', lazy=True)
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200))
    complete = db.Column(db.Boolean)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_completed = db.Column(db.DateTime)
    deadline = db.Column(db.DateTime, default=datetime.now)
    # completed_on = db.Column(db.DateTime)

    def __repr__(self):
        return '<Todo %r>' % self.id

############### Security & Admin Set Up ###############
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

# Create Admin
admin = Admin(app, name='ToDo', template_mode='bootstrap3')

############### Template Context ###############
def security_context_processor():
     return dict(
         admin_base_template=admin.base_template,
         admin_view=admin.index_view,
         h=admin_helpers,
     )
############### Model Views ###############
class UserView(ModelView):
    def is_accessible(self):
        return current_user.has_role('admin')
    form_base_class = SecureForm
    column_searchable_list = ['name', 'email']
    form_columns = ['name', 'email', 'password']
    # print("Hello")

class TodoView(ModelView):
    form_base_class = SecureForm
    column_searchable_list = ['text']

    # get current user, display items that match their name
    def get_query(self):
        return self.session.query(self.model).filter(self.model.user_id==current_user.id)

    # returns the number of items that match current_user.id so List(#) accurate
    def get_count_query(self):
        return self.session.query(func.count('*')).filter(self.model.user_id==current_user.id)

class RoleView(ModelView):
    def is_accessible(self):
        return current_user.has_role('admin')

class LoginMenuLink(MenuLink):
    def is_accessible(self):
        return not current_user.is_authenticated

class LogoutMenuLink(MenuLink):
    def is_accessible(self):
        return current_user.is_authenticated


# admin views
admin.add_view(UserView(User,db.session))
admin.add_view(TodoView(Todo, db.session))
admin.add_view(RoleView(Role, db.session))

# admin links
admin.add_link(LogoutMenuLink(name="Logout", category='', url="/logout"))
admin.add_link(LoginMenuLink(name='Login', category='', url="/login"))

############### Routes ###############
@app.route('/')
@login_required
def index():
    # @action('alert', 'Alert!', 'O.K.')
    # def
    return redirect('/admin')

if __name__ == '__main__':
    app.run(debug=True)
