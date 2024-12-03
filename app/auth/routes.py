from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user
from app import db
import string, random
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm
from app.models import User
from better_profanity import profanity

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        # Query using full_name for consistency
        full_name = f"{form.first_name.data} {form.last_name.data}".strip()
        user = User.query.filter(
            User.full_name == full_name,
            User.year == form.year.data
        ).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('Invalid name or password')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('main.index'))
    return render_template('auth/login.html', title='Sign In', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        key_stage_map = {
            '7': 'KS3', '8': 'KS3',
            '9': 'KS4', '10': 'KS4', '11': 'KS4',
            '12': 'KS5', '13': 'KS5'
        }
        key_stage = key_stage_map.get(form.year.data, 'Unknown')

        # Ensure no whitespace in full name
        first_name, last_name = form.first_name.data.strip(), form.last_name.data.strip()
        if ' ' in first_name or ' ' in last_name:
            flash('Please remove any whitespace from your name.')
            return redirect(url_for('auth.register'))

        full_name = f"{first_name} {last_name}"

        # Check for profanity
        if profanity.contains_profanity(full_name):
            flash('Unauthorized content detected in your name. Please try again.')
            return redirect(url_for('auth.register'))

        # Check if a user with the same full name and year already exists
        existing_user = User.query.filter(
            User.full_name == full_name,
            User.year == form.year.data
        ).first()
        
        if existing_user:
            flash('A user with this name and year already exists. Please use a different name or contact admin.')
            return redirect(url_for('auth.register'))
        
        # Create new user
        user = User(
            full_name=full_name,
            year=form.year.data, 
            key_stage=key_stage,
            maths_class=form.maths_class.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Register', form=form)

@bp.route('/register_admin', methods=['GET', 'POST'])
def register_admin():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        key_stage_map = {
            '7': 'KS3', '8': 'KS3',
            '9': 'KS4', '10': 'KS4', '11': 'KS4',
            '12': 'KS5', '13': 'KS5'
        }
        key_stage = key_stage_map.get(form.year.data, 'Unknown')

        first_name, last_name = form.first_name.data.strip(), form.last_name.data.strip()
        full_name = f"{first_name} {last_name}"

        # Check for profanity
        if profanity.contains_profanity(full_name):
            flash('Unauthorized content detected in your name. Please try again.')
            return redirect(url_for('auth.register_admin'))
        
        # Check if a user with the same full name and year already exists
        existing_user = User.query.filter(
            User.full_name == full_name,
            User.year == form.year.data
        ).first()
        
        if existing_user:
            flash('A user with this name and year already exists. Please use a different name or contact admin.')
            return redirect(url_for('auth.register_admin'))
        
        # Create new admin user
        user = User(
            full_name=full_name,
            year=form.year.data, 
            key_stage=key_stage,
            maths_class=form.maths_class.data,
            is_admin=True
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered admin!')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Register Admin', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))
