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

@bp.route('/challenge/<int:id>')
def challenge(id):
    challenge = Challenge.query.get_or_404(id)
    return render_template('main/challenge.html', title=challenge.title, challenge=challenge)

@bp.route('/articles')
def articles():
    articles = Article.query.filter_by(type='article').order_by(Article.date_posted.desc()).all()
    return render_template('main/articles.html', title='Articles', articles=articles)

@bp.route('/newsletters')
def newsletters():
    newsletters = Article.query.filter_by(type='newsletter').order_by(Article.date_posted.desc()).all()
    return render_template('main/newsletters.html', title='Newsletters', articles=newsletters)

@bp.route('/newsletter/<int:id>')
def newsletter(id):
    article = Article.query.get_or_404(id)
    return render_template('main/articles.html', title='Articles', articles=articles)

@bp.route('/article/<int:id>')
def article(id):
    article = Article.query.get_or_404(id)
    return render_template('main/article.html', title=article.title, article=article)

@bp.route('/leaderboard')
def leaderboard():
    entries = LeaderboardEntry.query.order_by(LeaderboardEntry.score.desc()).limit(10).all()
    return render_template('main/leaderboard.html', title='Leaderboard', entries=entries)