"""
Profile Routes Module
==================

This module contains routes for user profile management.

Dependencies:
------------
- Flask and related extensions
- SQLAlchemy for database operations
- Custom models and forms using Flask-WTF

Security:
---------
User profile management is handled securely:
1. Password changes are validated before updating
2. Account deletion requires user confirmation
3. User authentication is required for profile access

Maintenance Notes:
-----------------
1. Validate form data before processing it in routes.
2. Ensure privacy policy remains on profile page.
3. Deleting an account is irreversible and should be handled with caution, so ensure there is clear outlining of the consequences.
4. Password changes should be confirmed with the user before updating.
"""

from flask import render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import LeaderboardEntry, User
from app.profile import bp  # Import the blueprint
from app.profile.forms import ChangePasswordForm

# ====================
# Profile Routes
# ====================


@bp.route("/")  # Changed from '/profile' to '/' since we're using url_prefix
@login_required
def profile():
    """
    Display the user's profile page.

    Returns:
        Rendered profile page with user data and all leaderboard entries.
        
    Notes:
        - Now fetches all leaderboard entries for the user (one per key stage they've completed)
        - Template will need to handle multiple entries instead of a single entry
    """
    leaderboard_entries = LeaderboardEntry.query.filter_by(user_id=current_user.id).all()
    
    # Count
    length = len(leaderboard_entries)
    
    # Calculate total score across all key stages
    total_score = sum(entry.score for entry in leaderboard_entries)

    return render_template(
            "profile/main_profile.html", 
            title="Profile", 
            leaderboard_entries_count=length,
            total_score=total_score
    )


@bp.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    """
    Handle the user's password change process.

    Returns:
        Rendered change password page or redirects to profile upon successful password change.

    Notes:
    --------
        - Requires user authentication
        - Handles password change form validation
        - Flashes success message upon successful password change
    """
    if not current_user.is_authenticated:
        flash("You must be logged in to access this page.")
        return redirect(url_for("auth.login"))
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Invalid current password.", "error")
            return redirect(url_for("profile.change_password"))
        if form.current_password.data == form.new_password.data:
            flash("New password must be different from the current password.", "error")
            return redirect(url_for("profile.change_password"))
        if form.new_password.data != form.confirm_password.data:
            flash("Ensure both new passwords are the same", "error")
            return redirect(url_for("profile.change_password"))
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash("Your password has been updated.", "success")
        return redirect(url_for("profile.profile"))
    return render_template(
        "profile/change_password.html", title="Change Password", form=form
    )


@bp.route("/delete_account")
@login_required
def delete_account():
    """
    Handle the user account deletion process.

    Returns:
        Redirects to the home page upon successful account deletion.

    Notes:
    --------
        - Requires user authentication
        - Flashes success message upon successful account deletion

    Warning:
    --------
        - This action is irreversible and permanently deletes the user's account.
    """
    user = User.query.get(current_user.id)
    db.session.delete(user)
    db.session.commit()
    flash("Your account has been deleted.")
    return redirect(url_for("main.home"))
