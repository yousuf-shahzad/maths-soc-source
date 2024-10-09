from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app import db
from app.admin import bp
from app.models import Article, Challenge, User
from app.admin.forms import ChallengeForm, ArticleReviewForm, NewsletterForm

@bp.route('/admin')
@login_required
def admin_index():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    return render_template('admin/index.html', title='Admin Dashboard')

@bp.route('/admin/create_newsletter', methods=['GET', 'POST'])
@login_required
def create_newsletter():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    
    form = NewsletterForm()
    if form.validate_on_submit():
        newsletter = Article(title=form.title.data, 
                             content=form.content.data, 
                             user_id=current_user.id, 
                             is_approved=True, 
                             is_newsletter=True)
        db.session.add(newsletter)
        db.session.commit()
        flash('Newsletter created successfully.')
        return redirect(url_for('admin.manage_articles'))
    
    return render_template('admin/create_newsletter.html', title='Create Newsletter', form=form)

@bp.route('/admin/challenges', methods=['GET', 'POST'])
@login_required
def manage_challenges():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    form = ChallengeForm()
    if form.validate_on_submit():
        challenge = Challenge(title=form.title.data, content=form.content.data)
        db.session.add(challenge)
        db.session.commit()
        flash('Challenge added successfully.')
        return redirect(url_for('admin.manage_challenges'))
    challenges = Challenge.query.order_by(Challenge.date_posted.desc()).all()
    return render_template('admin/manage_challenges.html', title='Manage Challenges', form=form, challenges=challenges)

@bp.route('/admin/challenges/edit/<int:challenge_id>', methods=['GET', 'POST'])
@login_required
def edit_challenge(challenge_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    
    challenge = Challenge.query.get_or_404(challenge_id)
    form = ChallengeForm(obj=challenge)

    if form.validate_on_submit():
        challenge.title = form.title.data
        challenge.content = form.content.data
        db.session.commit()
        flash('Challenge updated successfully.')
        return redirect(url_for('admin.manage_challenges'))
    
    return render_template('admin/edit_challenge.html', title='Edit Challenge', form=form)
    
@bp.route('/admin/challenges/delete/<int:challenge_id>')
@login_required
def delete_challenge(challenge_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    
    challenge = Challenge.query.get_or_404(challenge_id)
    db.session.delete(challenge)
    db.session.commit()
    flash('Challenge deleted successfully.')
    return redirect(url_for('admin.manage_challenges'))

@bp.route('/admin/articles')
@login_required
def manage_articles():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    articles = Article.query.filter_by(is_approved=False).order_by(Article.date_posted.desc()).all()
    return render_template('admin/manage_articles.html', title='Manage Articles', articles=articles)

@bp.route('/admin/approve_article/<int:id>')
@login_required
def approve_article(id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    article = Article.query.get_or_404(id)
    article.is_approved = True
    db.session.commit()
    flash('Article approved.')
    return redirect(url_for('admin.manage_articles'))

@bp.route('/admin/toggle_admin/<int:user_id>')
@login_required
def toggle_admin(user_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    flash(f'Admin status for {user.username} has been toggled.')
    return redirect(url_for('admin.manage_users'))

@bp.route('/admin/manage_users')
@login_required
def manage_users():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    users = User.query.all()
    return render_template('admin/manage_users.html', title='Manage Users', users=users)

@bp.route('/admin/manage_users/delete/<int:user_id>')
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.')
    return redirect(url_for('admin.manage_users'))
