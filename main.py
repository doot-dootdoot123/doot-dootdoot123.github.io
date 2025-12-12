from flask import Flask, render_template, redirect, url_for,session
from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired
from wtforms import StringField, SubmitField, PasswordField, EmailField,FileField, DateField, IntegerField
from wtforms.fields.choices import SelectField
from wtforms.validators import DataRequired
import random
import os
from datetime import datetime, date

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
image_directory = "static/images"
imagefiles = [f for f in os.listdir(image_directory) if os.path.isfile(os.path.join(image_directory,f))]
app.secret_key = "yes"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(64),unique = True, nullable = False)
    email = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    usercards = db.relationship("UserCard", back_populates="user", cascade="all, delete-orphan")
    Tasks = db.relationship("Task", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    taskname = db.Column(db.String(64), nullable = False)
    priority = db.Column(db.String(64), nullable = False)
    datedue = db.Column(db.Date(), nullable = False)
    weeknum = db.Column(db.Integer, nullable=False)
    completed = db.Column(db.Boolean, nullable = False, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable = False)
    user = db.relationship("User", back_populates="Tasks")

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_name = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    rarity = db.Column(db.String(64), nullable=False)
    era = db.Column(db.String(64), nullable=False)
    group = db.Column(db.String(64), nullable=False)

    usercards = db.relationship("UserCard", back_populates="card")

class UserCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    card_id = db.Column(db.Integer, db.ForeignKey("card.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)


    user = db.relationship("User", back_populates="usercards")
    card = db.relationship("Card", back_populates="usercards")


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class DeleteCard(FlaskForm):
    cardid = IntegerField('Card ID', validators=[DataRequired()])
    submit = SubmitField('Delete')

class RegisterForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    comfirmpassword = PasswordField("Comfirm Password", validators=[DataRequired()])
    submit = SubmitField('Register')

class addtask(FlaskForm):
    taskname = StringField("task name", validators=[DataRequired()])
    priority = SelectField("priority", choices=[('highprio', 'High priority'),
                                        ('medprio', 'Medium priority'),
                                                ('lowprio', 'Low priority')],validators=[DataRequired()])
    datedue = DateField("date due", validators=[DataRequired()])
    submit = SubmitField('Add')

class addcard(FlaskForm):
    person_name = StringField("person name", validators=[DataRequired()])
    imagefile = FileField('image', validators=[FileRequired()])
    era = StringField("era", validators=[DataRequired()])
    rarity = StringField("rarity", validators=[DataRequired()])
    group = StringField("group", validators=[DataRequired()])
    submit = SubmitField('Add')

#-------------------------------------------------------------------------#
@app.route('/')
def index():
    return render_template("index.html")
@app.route('/home/<usero>')
def home(usero):
    # Get the user object
    user_obj = User.query.filter_by(username=usero).first()
    if user_obj:
        # Get all tasks for this user
        tasklist = Task.query.filter_by(user_id=user_obj.id).order_by(Task.completed.asc()).all()

    else:
        tasklist = []
    return render_template('oh.html', tasklist=tasklist, user=user_obj)

@app.route('/today/<usero>')
def today(usero):
    todayo = date.today()
    userobj = User.query.filter_by(username=usero).first()
    if userobj:
        tasklist = Task.query.filter_by(datedue=todayo).order_by(Task.completed.asc()).all()
    else:
        tasklist = []
    return render_template('today.html', tasklist = tasklist, user=userobj)

@app.route('/week/<usero>')
def week(usero):
    weeko = datetime.today().isocalendar()[1]
    userobj = User.query.filter_by(username=usero).first()
    if userobj:
        tasklist = Task.query.filter_by(weeknum=weeko).order_by(Task.completed.asc()).all()
        print(tasklist)
    else:
        tasklist = []
    return render_template('week.html', tasklist = tasklist, user=userobj)
#------------------------------------------------------------------------#

@app.route('/apptasks/<username>', methods=['GET', 'POST'])
def add_tasks(username):
    form = addtask()
    user_obj = User.query.filter_by(username=username).first()
    if form.validate_on_submit() and user_obj:
        taskname = form.taskname.data
        priority = form.priority.data
        datedue = form.datedue.data
        weeknum = datedue.isocalendar()[1]
        task = Task(taskname=taskname, priority=priority, datedue = datedue, weeknum=weeknum, user_id=user_obj.id)
        db.session.add(task)
        db.session.commit()
        return redirect(url_for('home', usero=user_obj.username))
    return render_template('addtasks.html', form=form, user = user_obj.username)


@app.route("/login",methods=["GET","POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['username'] = user.username
            usernamep = user.username
            return redirect(url_for("home",usero=usernamep))
        else:
            return render_template("login.html", form=form)
    return render_template("login.html", form=form)

@app.route("/signup",methods=["GET","POST"])
def signup():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        user = User(username=username, email=email,password_hash=generate_password_hash(password))
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login", username=username))
    return render_template("signup.html", form=form)

@app.route("/getcard/<int:task_id>")
def getcard(task_id):
    task = Task.query.get(task_id)
    if task:
        task.completed = True
        db.session.commit()
        user_obj = task.user

        cards = Card.query.all()
        chard = random.choice(cards)
        cardduplicate = UserCard.query.filter_by(user_id=user_obj.id, id=chard.id).first()
        if cardduplicate:
            cardduplicate.quantity += 1
            quantity = cardduplicate.quantity
        else:
            cardo = UserCard(user_id=user_obj.id, card_id=chard.id, quantity=1, tasklinked=task)
            quantity = 1
            db.session.add(cardo)
        db.session.commit()

        imagepath = f"images/{chard.image_name}"


        return render_template("card.html", image=imagepath,name=chard.name,rarity=chard.rarity,group=chard.group, usero=user_obj.username, quantity=quantity, era = chard.era)
    return redirect(url_for("home", username=session.get('username')))

@app.route("/collection/<user>")
def collection(user):
    usero = User.query.filter_by(username=user).first()
    if not usero:
        return redirect(url_for('login'))
    cards = UserCard.query.filter_by(user_id=usero.id).all()
    return render_template("collection.html",cards=cards,user=user)

@app.route("/adcard",methods=["GET","POST"])
def adcard():
    form = addcard()

    # make sure the user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))

    # get the logged in user
    user_obj = User.query.filter_by(username=session['username']).first()
    if not user_obj:
        return redirect(url_for('login'))

    if form.validate_on_submit():
        person_name = form.person_name.data
        imagefile = form.imagefile.data
        era = form.era.data
        rarity = form.rarity.data
        group = form.group.data

        imagefilename = imagefile.filename
        imagepath = os.path.join("static/images", imagefilename)
        imagefile.save(imagepath)

        doot = Card(
            image_name=imagefilename,
            name=person_name,
            rarity=rarity,
            era=era,
            group=group,
        )
        db.session.add(doot)
        db.session.commit()

        return redirect(url_for('home', usero=user_obj.username))
    return render_template("adcard.html",form=form)

@app.route("/deletedacarddo", methods=["GET","POST"])
def deletecard():
    if 'username' not in session:
        return (redirect(url_for('login')))
    form = DeleteCard()
    if form.validate_on_submit():
        cardtoremove = Card.query.filter_by(id=form.cardid.data).first()
        if cardtoremove:
            db.session.delete(cardtoremove)
            cards = UserCard.query.filter_by(card_id = form.cardid.data).all()
            for card in cards:
                db.session.delete(card)
            db.session.commit()
            return redirect(url_for('home', usero=session['username']))
    return render_template("deletecard.html",form=form)

with app.app_context():
    db.create_all()
if __name__ == '__main__':
    app.run(debug=True)
