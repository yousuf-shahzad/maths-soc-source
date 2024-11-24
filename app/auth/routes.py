from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user
from app import db
import string, random
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm
from app.models import User

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('main.index'))
    return render_template('auth/login.html', title='Sign In', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

# ! REGISTER ROUTS

@bp.route('/register_admin', methods=['GET', 'POST'])
def register_admin():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        if form.year.data == '7' or form.year.data == '8' or form.year.data == '9':
            key_stage = 'KS3'
        elif form.year.data == '10' or form.year.data == '11':
            key_stage = 'KS4'
        elif form.year.data == '12' or form.year.data == '13':
            key_stage = 'KS5'
        print(key_stage)
        user = User(username=form.username.data, year=form.year.data, key_stage=key_stage, is_admin=True)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Register', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        if form.year.data == '7' or form.year.data == '8':
            key_stage = 'KS3'
        elif form.year.data == '10' or form.year.data == '11' or form.year.data == '9':
            key_stage = 'KS4'
        elif form.year.data == '12' or form.year.data == '13':
            key_stage = 'KS5'
        print(key_stage)
        user = User(username=form.username.data, year=form.year.data, key_stage=key_stage)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Register', form=form)

# WE DON'T SERVE THIS ROUTE ANYMORE BECAUSE WE HAVE ADMIN ROUTES NOW AND WE DON'T NEED USERS TO REGISTER, JUST ADMINS
# LEAVING THIS HERE IN THE EVENTUALITY THAT WE WANT TO ALLOW USERS TO REGISTER AGAIN

# oignore him we do serve these routes Now.