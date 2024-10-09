from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length

class ChallengeForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=100)])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Create Challenge')

class NewsletterForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=100)])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Create Newsletter')

class ArticleReviewForm(FlaskForm):
    approve = BooleanField('Approve')
    submit = SubmitField('Submit Review')