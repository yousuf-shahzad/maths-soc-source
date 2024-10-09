from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app import db
from app.main import bp
from app.models import Challenge, Article, LeaderboardEntry

@bp.route('/')
@bp.route('/index')
def index():
    return render_template('index.html', title='Home')

@bp.route('/challenges')
def challenges():
    challenges = Challenge.query.order_by(Challenge.date_posted.desc()).all()
    return render_template('main/challenges.html', title='Challenges', challenges=challenges)

@bp.route('/articles')
def articles():
    articles = Article.query.filter_by(is_approved=True).order_by(Article.date_posted.desc()).all()
    return render_template('main/articles.html', title='Articles', articles=articles)

@bp.route('/leaderboard')
def leaderboard():
    entries = LeaderboardEntry.query.order_by(LeaderboardEntry.score.desc()).limit(10).all()
    return render_template('main/leaderboard.html', title='Leaderboard', entries=entries)