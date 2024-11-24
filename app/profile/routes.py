from flask import render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import LeaderboardEntry
from app.profile import bp  # Import the blueprint

@bp.route('/')  # Changed from '/profile' to '/' since we're using url_prefix
@login_required
def profile():
    leaderboard_data = LeaderboardEntry.query.filter_by(user_id=current_user.id).first()
    return render_template('profile/main_profile.html', title='Profile', leaderboard_data=leaderboard_data)