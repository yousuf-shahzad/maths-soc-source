from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length


class ChangePasswordForm(FlaskForm):
    current_password = StringField(
        'Current Password', validators=[DataRequired()])
    new_password = StringField('Password', validators=[DataRequired()])
    confirm_password = StringField(
        'Repeat Password', validators=[DataRequired()])
    submit = SubmitField('Change Password')
