from flask import Flask, g, render_template, flash, redirect, url_for, abort
from flask_bcrypt import check_password_hash
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)


import forms
import models

DEBUG = True
PORT = 8000
HOST = "0.0.0.0"

app = Flask(__name__)
app.secret_key = "auoesh.bouoastuh.43,uoausoehuosth3ououea.auoub!"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(userid):
    try:
        return models.User.get(models.User.id == userid)
    except models.DoesNotExist:
        return None


@app.before_request
def before_request():
    """Connect to the database before each request."""
    g.db = models.DATABASE
    g.db.connect()
    g.user = current_user


@app.after_request
def after_request(response):
    """Close the database connection after each request."""
    g.db.close()
    return response


@app.route("/login", methods=("GET", "POST"))
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        try:
            user = models.User.get(models.User.email == form.email.data)
        except models.DoesNotExist:
            flash("Your email or password doesn't match!", "error")
        else:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                flash("You've been logged in!", "success")
                return redirect(url_for("index"))
            else:
                flash("Your email or password doesn't match!", "error")
    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You've been logged out! Come back soon!", "success")
    return redirect(url_for("index"))


@app.route("/")
def index():
    stream = models.Post.select().limit(4)
    return render_template("index.html", stream=stream)


@app.route("/entries")
def entries():
    stream = models.Post.select().limit(3)
    return render_template("all_entries.html", stream=stream)


@app.route("/new_post", methods=("GET", "POST"))
@login_required
def post():
    form = forms.PostForm()
    if form.validate_on_submit():
        models.Post.create(
            user=g.user.id,
            content=form.content.data.strip(),
            title=form.title.data,
            time_spent=form.time_spent.data,
            resources=form.resources.data,
            tags=form.tags.data,
        )
        flash("Journal Entry done!", "success")
        return redirect(url_for("index"))
    return render_template("new.html", form=form)


@app.route("/entries/edit/<post_id>", methods=["GET", "POST"])
def edit(post_id=None):
    post = models.Post.get(models.Post.id == post_id)
    form = forms.PostForm()
    if form.validate_on_submit():
        models.Post.update(
            title=form.title.data.strip(),
            time_spent=form.time_spent.data,
            content=form.content.data.strip(),
            resources=form.resources.data.strip(),
            tags=form.tags.data.strip(),
        ).where(models.Post.id == post_id).execute()
        flash("Entry saved!", "success")
        return redirect(url_for("index"))
    form.title.data = post.title
    form.time_spent.data = post.time_spent
    form.content.data = post.content
    form.resources.data = post.resources
    form.tags.data = post.tags
    return render_template("edit.html", form=form)


@app.route("/entries/delete/<post_id>")
def delete(post_id=None):
    models.Post.get(models.Post.id == post_id).delete_instance()
    flash("Deleted!", "success")
    return redirect(url_for("index"))


@app.route("/post/<int:post_id>")
def view_post(post_id):
    posts = models.Post.select().where(models.Post.id == post_id)
    if posts.count() == 0:
        abort(404)
    return render_template("detail.html", stream=posts)


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    models.initialize()
    try:
        models.User.create_user(
            username="dundermiflin",
            email="aaron@ajeema.com",
            password="password",
            admin=True,
        )
    except ValueError:
        pass
    app.run(debug=DEBUG, host=HOST, port=PORT)
