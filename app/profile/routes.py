from flask import render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import LeaderboardEntry, User
from app.profile import bp  # Import the blueprint
from app.profile.forms import ChangePasswordForm

@bp.route('/')  # Changed from '/profile' to '/' since we're using url_prefix
@login_required
def profile():
    leaderboard_data = LeaderboardEntry.query.filter_by(user_id=current_user.id).first()
    return render_template('profile/main_profile.html', title='Profile', leaderboard_data=leaderboard_data)

@bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if not current_user.is_authenticated:
        flash('You must be logged in to access this page.')
        return redirect(url_for('auth.login'))
    form = ChangePasswordForm()
    if form.validate_on_submit():
        current_user.set_password(form.new_password.data)
        flash('Your password has been updated.')
        return redirect(url_for('profile.profile'))
    return render_template('profile/change_password.html', title='Change Password', form=form)

@bp.route('/delete_account')
@login_required
def delete_account():
    user = User.query.get(current_user.id)
    db.session.delete(user)
    db.session.commit()
    flash('Your account has been deleted.')
    return redirect(url_for('main.index'))