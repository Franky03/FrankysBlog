from flask import Flask, render_template, redirect, url_for, flash, abort, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterForm, LoginForm, ContactForm, CommentForm
from flask_gravatar import Gravatar
from functools import wraps
import smtplib
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
ckeditor = CKEditor(app)
gravatar= Gravatar(app,size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False, base_url=None)
Bootstrap(app)

##CONNECT TO DB

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///blog.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#LOGIN MANAGER

login_manager= LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

##CONFIGURE TABLES

class User(UserMixin, db.Model):
    __tablename__= "users"
    id= db.Column(db.Integer, primary_key= True)
    email= db.Column(db.String(100), unique= True)
    password= db.Column(db.String(100))
    name = db.Column(db.String(100))
    
    #ADD PARENT RELATIONSHIP 
    #(Fazendo a relação Parent and Child com as outras tables)

    #"author" refers to the author property in BlogPost class.
    posts= relationship("BlogPost", back_populates= "author")
    #"comment_author" refers to the comment_author property in the Comment class.
    comments= relationship("Comment", back_populates= "comment_author")


class BlogPost(db.Model):
    __tablename__= "blog_posts"
    id = db.Column(db.Integer, primary_key=True)

    #Create Foreign Key, "users.id" the users refers to the tablename of User.
    author_id= db.Column(db.Integer, db.ForeignKey("users.id"))
    #Create reference to the User object, the "posts" refers to the posts property in the User Class
    author = relationship("User", back_populates="posts")

    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    #PARENT RELATIONSHIP
    #"parent_post" refers to the parent_post property in the Comment class
    comments= relationship("Comment", back_populates= "parent_post")

class Comment(db.Model):
    __tablename__= "comments"
    id= db.Column(db.Integer, primary_key= True)

    #ADD CHILD RELATIONSHIPS
    # "comments" refers to the comments property in the User and BlogPost classes.

    #Users
    author_id= db.Column(db.Integer, db.ForeignKey("users.id"))
    comment_author= relationship("User", back_populates= "comments")

    #Blog Posts
    post_id= db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    parent_post= relationship("BlogPost", back_populates= "comments")

    text= db.Column(db.Text, nullable= False)

db.create_all()

#ADMIM ONLY FUNCTION
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #Se o usuário atual for diferente do admin
        if not current_user.is_authenticated or current_user.id != 1:
            # retorna abort 403
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

#SEND EMAIL/ CONTACT ME

def send_email(name, email, phone, text):
    email_message= f"Subject:New Message\n\nName:{name}\nEmail: {email}\nPhone: {phone}\nMessage: \n{text}"

    my_email= "aulapython@yahoo.com"
    my_password= os.environ.get("EMAIL_KEY")

    with smtplib.SMTP('smtp.mail.yahoo.com', port=587) as connection:
        connection.starttls()
        connection.login(my_email, my_password)
        connection.sendmail(my_email, "genasagari6@gmail.com", msg= email_message)

#ROUTES

@app.route('/')
def get_all_posts():
    posts= db.session.query(BlogPost).all()
    return render_template("index.html", all_posts=posts)

@app.route("/register", methods= ["GET", "POST"])
def register():
    form= RegisterForm()

    if form.validate_on_submit():

        if User.query.filter_by(email= form.email.data).first():
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for("login"))

        new_user= User(
            email= form.email.data,
            password= generate_password_hash(password= form.password.data, 
            method="pbkdf2:sha256", salt_length=8),
            name= form.name.data
        )

        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)

        return redirect(url_for("get_all_posts"))
        
    return render_template("register.html", form= form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form= LoginForm()
    if form.validate_on_submit():
        email= form.email.data
        password= form.password.data
        
        user= User.query.filter_by(email= email).first()
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for("login"))
        
        elif not check_password_hash(user.password, password):
            flash("Password incorrect, please try again.")
            return redirect(url_for("login"))
        
        else:
            login_user(user=user)
            return redirect(url_for("get_all_posts"))

    return render_template("login.html", form= form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("get_all_posts"))

@app.route("/post/<int:index>", methods=["GET", "POST"])
def show_post(index):
    requested_post= BlogPost.query.get(index)
    form= CommentForm()
    if form.validate_on_submit():

        new_comment= Comment(
            text= form.comment.data,
            comment_author= current_user,
            parent_post= requested_post
        )

        db.session.add(new_comment)
        db.session.commit()
    return render_template("post.html", post=requested_post, form= form)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact", methods= ["GET","POST"])
def contact():
    form= ContactForm()
    h1_text= "Contact Me"
    
    if form.validate_on_submit():
        try:
            send_email(form.name.data, form.email.data, form.phone.data, form.message.data)
            h1_text= "Successfully sent your message"
        except:
            h1_text= "Unsuccessfully sent your message"

    return render_template("contact.html", big_text= h1_text, form= form)

@app.route("/edit/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post= BlogPost.query.get(post_id)

    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        body=post.body
    )

    if edit_form.validate_on_submit():
        post.title= edit_form.title.data
        post.subtitle= edit_form.subtitle.data
        post.img_url= edit_form.img_url.data
        post.body= edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", index= post_id))
    return render_template("make-post.html", form=edit_form, is_edit= True)

@app.route("/new-post", methods=["GET","POST"])
@admin_only
def new_post():
    form= CreatePostForm()
    if form.validate_on_submit():
        new_blog= BlogPost(
            title= form.title.data,
            subtitle= form.subtitle.data,
            author= current_user,
            img_url= form.img_url.data,
            body= form.body.data,
            date= date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_blog)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form= form)

@app.route("/delete/<int:post_id>")
@admin_only
def delete(post_id):
    blog_to_delete=BlogPost.query.get(post_id)
    db.session.delete(blog_to_delete)
    db.session.commit()
    return redirect(url_for("get_all_posts"))

@app.route("/delcomment/<int:post_id>/<int:comment_id>/")
@admin_only
def delete_comment(comment_id, post_id):
    comment_to_delete= Comment.query.get(comment_id)
    db.session.delete(comment_to_delete)
    db.session.commit()
    return redirect(url_for("show_post", index= post_id))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)