"""
Auth Routes Module
==================

This module contains routes for user authentication and registration.
It is organized into logical sections based on functionality:
- Login Routes
- Registration Routes
- Logout Route

Dependencies:
------------
- Flask and related extensions
- SQLAlchemy for database operations
- Custom models and forms using Flask-WTF
- Better Profanity for content filtering

Security:
---------
User authentication and registration are handled securely:
1. Passwords are hashed before storing in the database
2. Profanity checks are performed on user names
3. Duplicate registrations are prevented
4. Admin registration is disabled in production

Maintenance Notes:
-----------------
1. Ensure that the user model is up-to-date with the database schema.
2. Validate form data before processing it in routes.
3. Use secure practices for user authentication and registration.
4. Keep the registration process simple and user-friendly.
5. Disable admin registration in production environments.
"""

from flask import render_template, flash, redirect, url_for
from flask_login import login_user, logout_user, current_user
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm
from app.models import User
from better_profanity import profanity
from config import Config

# ====================
# Login Routes
# ====================


@bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Handle user login process.

    Returns:
        Rendered login page or redirects to index upon successful authentication.

    Notes:
        - Redirects authenticated users to index
        - Authenticates users by full name and year
        - Handles login form validation
        - Flashes error for invalid credentials
    """
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    form = LoginForm()
    if form.validate_on_submit():
        # Query using full_name for consistency
        full_name = f"{form.first_name.data} {form.last_name.data}".strip()
        user = User.query.filter(
            User.full_name == full_name, User.year == form.year.data
        ).first()

        if user is None or not user.check_password(form.password.data):
            flash("Invalid name or password")
            return redirect(url_for("auth.login"))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for("main.home"))
    return render_template("auth/login.html", title="Sign In", form=form)


# ====================
# Registration Routes
# ====================


@bp.route("/register", methods=["GET", "POST"])
def register():
    """
    Handle user registration process.

    Returns:
        Rendered registration page or redirects to login upon successful registration.

    Notes:
        - Redirects authenticated users to index
        - Maps school years to key stages
        - Validates user input for name and registration
        - Prevents duplicate registrations
        - Checks for inappropriate content in names
    """
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    form = RegistrationForm()
    if form.validate_on_submit():
        key_stage_map = {
            "7": "KS3",
            "8": "KS3",
            "9": "KS4",
            "10": "KS4",
            "11": "KS4",
            "12": "KS5",
            "13": "KS5",
        }
        key_stage = key_stage_map.get(form.year.data, "Unknown")

        # Ensure no whitespace in full name
        first_name, last_name = (
            form.first_name.data.strip(),
            form.last_name.data.strip(),
        )
        if " " in first_name or " " in last_name:
            flash("Please remove any whitespace from your name.")
            return redirect(url_for("auth.register"))

        full_name = f"{first_name} {last_name}"

        # Check for profanity
        if profanity.contains_profanity(full_name):
            flash("Unauthorized content detected in your name. Please try again.")
            return redirect(url_for("auth.register"))

        # Check if a user with the same full name and year already exists
        existing_user = User.query.filter(
            User.full_name == full_name, User.year == form.year.data
        ).first()

        if existing_user:
            flash(
                "A user with this name and year already exists. Please use a different name or contact admin."
            )
            return redirect(url_for("auth.register"))

        # Create new user
        user = User(
            full_name=full_name,
            year=form.year.data,
            key_stage=key_stage,
            maths_class=form.maths_class.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Congratulations, you are now a registered user!")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", title="Register", form=form)


if not Config.is_production():
    @bp.route("/register_admin", methods=["GET", "POST"])
    def register_admin():
        """
        Handle admin user registration process.

        Returns:
            Rendered admin registration page or redirects to login upon successful registration.

        Notes:
            - Only available in non-production environments
            - Creates users with admin privileges
            - Prevents duplicate registrations
            - Validates user input
        """
        if current_user.is_authenticated:
            return redirect(url_for("main.home"))
        form = RegistrationForm()
        if form.validate_on_submit():
            key_stage_map = {
                "7": "KS3", "8": "KS3", 
                "9": "KS4", "10": "KS4", "11": "KS4", 
                "12": "KS5", "13": "KS5"
            }
            key_stage = key_stage_map.get(form.year.data, "Unknown")

            first_name, last_name = (
                form.first_name.data.strip(),
                form.last_name.data.strip(),
            )
            full_name = f"{first_name} {last_name}"

            # Check for profanity
            if profanity.contains_profanity(full_name):
                flash("Unauthorized content detected in your name. Please try again.")
                return redirect(url_for("auth.register_admin"))

            # Check if a user with the same full name and year already exists
            existing_user = User.query.filter(
                User.full_name == full_name, User.year == form.year.data
            ).first()

            if existing_user:
                flash(
                    "A user with this name and year already exists. Please use a different name or contact admin."
                )
                return redirect(url_for("auth.register_admin"))

            # Create new admin user
            user = User(
                full_name=full_name,
                year=form.year.data,
                key_stage=key_stage,
                maths_class=form.maths_class.data,
                is_admin=True,
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash("Congratulations, you are now a registered admin!")
            return redirect(url_for("auth.login"))
        return render_template("auth/register.html", title="Register Admin", form=form)
else:
    @bp.route("/register_admin", methods=["GET", "POST"])
    def register_admin():
        """
        Disabled admin registration route in production.
        
        Returns:
            Redirects to the main index page with a warning message.
        """
        flash("Admin registration is disabled in production environments.")
        return redirect(url_for("main.home"))

# ====================
# Logout Route
# ====================


@bp.route("/logout")
def logout():
    """
    Handle user logout process.

    Returns:
        Redirect to the main index page after logging out the current user.

    Notes:
        - Terminates the current user's session
        - Provides a clean logout experience
    """
    logout_user()
    return redirect(url_for("main.home"))
