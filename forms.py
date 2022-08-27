from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField,EmailField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField


class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    #Mudar o StringField do body para CKEditorField
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")

class RegisterForm(FlaskForm):
    email= EmailField("Email", validators=[DataRequired()])
    password= PasswordField("Password", validators=[DataRequired()])
    name= StringField("Name", validators=[DataRequired()])
    submit= SubmitField("Sign Me Up!")

class LoginForm(FlaskForm):
    email= EmailField("Email", validators=[DataRequired()])
    password= PasswordField("Password", validators=[DataRequired()])
    submit= SubmitField("Let Me In!")

class ContactForm(FlaskForm):
    name= StringField("Name", validators=[DataRequired()])
    email= EmailField("Email", validators=[DataRequired()])
    phone= StringField("Phone Number", validators=[DataRequired()])
    message= CKEditorField("Message", validators=[DataRequired()])
    submit= SubmitField("Send")

class CommentForm(FlaskForm):
    comment= CKEditorField("Comment", validators=[DataRequired()])
    submit= SubmitField("Submit Comment")