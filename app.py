import os
import uuid
from flask import Flask, session, render_template, request, Response, redirect, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from db import db_init, db
from models import User, Automobile
from datetime import datetime
from flask_session import Session
from helpers import login_required

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///items.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db_init(app)

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# static file path
@app.route("/static/<path:path>")
def static_dir(path):
    return send_from_directory("static", path)


# signup as seller
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        session.clear()
        password = request.form.get("password")
        repassword = request.form.get("repassword")
        if (password != repassword):
            return render_template("error.html", message="Passwords do not match!")

        # hash password
        pw_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

        fullname = request.form.get("fullname")
        username = request.form.get("username")
        # store in database
        new_user = User(fullname=fullname, username=username, password=pw_hash)
        try:
            db.session.add(new_user)
            db.session.commit()
        except:
            return render_template("error.html", message="Username already exists!")
        return render_template("login.html", msg="Account created!")
    return render_template("signup.html")


# login as merchant
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session.clear()
        username = request.form.get("username")
        password = request.form.get("password")
        result = User.query.filter_by(username=username).first()
        print(result)
        # Ensure username exists and password is correct
        if result == None or not check_password_hash(result.password, password):
            return render_template("error.html", message="Invalid username and/or password")
        # Remember which user has logged in
        session["username"] = result.username
        return redirect("/home")
    return render_template("login.html")


# logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# view all cars
@app.route("/")
def index():
    rows = Automobile.query.all()
    return render_template("index.html", rows=rows)


# seller home page to add new cars and edit cars put on site
@app.route("/home", methods=["GET", "POST"], endpoint='home')
@login_required
def home():
    if request.method == "POST":
        image = request.files['image']
        filename = str(uuid.uuid1()) + os.path.splitext(image.filename)[1]
        image.save(os.path.join("static/images", filename))
        category = request.form.get("category")
        make_model = request.form.get("make_model")
        status = request.form.get("status")
        description = request.form.get("description")
        price_range = request.form.get("price_range")
        contact = request.form.get("contact")
        new_pro = Automobile(category=category, make_model=make_model, status=status, description=description, price_range=price_range,
                          contact=contact, filename=filename, username=session['username'])
        db.session.add(new_pro)
        db.session.commit()
        rows = Automobile.query.filter_by(username=session['username'])
        return render_template("home.html", rows=rows, message="Listing added")

    rows = Automobile.query.filter_by(username=session['username'])
    return render_template("home.html", rows=rows)


# when edit listing option is selected this function is utilized
@app.route("/edit/<int:pro_id>", methods=["GET", "POST"], endpoint='edit')
@login_required
def edit(pro_id):
    # select only the editing product from db
    result = Automobile.query.filter_by(pro_id=pro_id).first()
    if request.method == "POST":
        # throw error when some merchant tries to edit product of other merchant
        if result.username != session['username']:
            return render_template("error.html", message="You are not authorized to edit this listing")
        category = request.form.get("category")
        make_model = request.form.get("make_model")
        description = request.form.get("description")
        price_range = request.form.get("price_range")
        contact = request.form.get("contact")
        status = request.form.get("status")
        result.status = status
        result.category = category
        result.make_model = make_model
        result.description = description
        result.contact = contact
        result.price_range = price_range
        db.session.commit()
        rows = Automobile.query.filter_by(username=session['username'])
        return render_template("home.html", rows=rows, message="Listing edited")
    return render_template("edit.html", result=result)