from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length


class ArticleForm(FlaskForm):
    title = StringField('Title', validators=[
                        DataRequired(), Length(min=1, max=100)])
    author = StringField('Title', validators=[
                         DataRequired(), Length(min=1, max=100)])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Submit Article')
