import os
from werkzeug.utils import secure_filename
from flask import render_template, flash, redirect, url_for, request, send_from_directory, current_app
from flask_login import login_required, current_user
from flask_ckeditor import upload_success, upload_fail
from app import db, Config
from app.admin import bp
from app.models import Article, Challenge, User
from app.admin.forms import ChallengeForm, ArticleForm

@bp.route('/admin')
@login_required
def admin_index():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    return render_template('admin/index.html', title='Admin Dashboard')

# ! ARTICLE ROUTES

@bp.route('/admin/articles/create', methods=['GET', 'POST'])
@login_required
def create_article():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    
    form = ArticleForm()
    if form.validate_on_submit():
        article = Article(title=form.title.data, 
                          content=form.content.data, 
                          named_creator=form.author.data,
                          user_id=current_user.id, 
                          type=form.type.data or 'article')
        db.session.add(article)
        db.session.commit()
        flash(f'{form.type.data.capitalize()} created successfully.')
        return redirect(url_for('admin.manage_articles'))
    
    return render_template('admin/create_article.html', title='Create Article/Newsletter', form=form)

@bp.route('/admin/articles')
@login_required
def manage_articles():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    articles = Article.query.order_by(Article.date_posted.desc()).all()
    return render_template('admin/manage_articles.html', title='Manage Articles and Newsletters', articles=articles)

@bp.route('/admin/articles/delete/<int:article_id>')
@login_required
def delete_article(article_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    
    article = Article.query.get_or_404(article_id)
    db.session.delete(article)
    db.session.commit()
    
    flash(f'{article.type.capitalize()} deleted successfully.')
    return redirect(url_for('admin.manage_articles'))

# ! CHALLENGE ROUTES

from flask import current_app, flash, redirect, url_for, render_template
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os

@bp.route('/admin/challenges/create', methods=['GET', 'POST'])
@login_required
def create_challenge():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('main.index'))

    form = ChallengeForm()
    if form.validate_on_submit():
        try:
            challenge = Challenge(title=form.title.data, content=form.content.data)

            if form.image.data:
                try:
                    filename = secure_filename(form.image.data.filename)
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    
                    # Ensure the upload folder exists
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    form.image.data.save(file_path)
                    challenge.file_url = filename
                except IOError as e:
                    current_app.logger.error(f"File save error: {str(e)}")
                    flash('Error saving the image file. Please try again.', 'error')
                    return render_template('admin/create_challenge.html', title='Create Challenge', form=form)

            db.session.add(challenge)
            db.session.commit()
            flash('Challenge added successfully.', 'success')
            return redirect(url_for('admin.manage_challenges'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating challenge: {str(e)}")
            flash('An error occurred while creating the challenge. Please try again.', 'error')

    return render_template('admin/create_challenge.html', title='Create Challenge', form=form)

@bp.route('/static/uploads/<path:filename>')
@login_required
def uploaded_files(filename):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    print("asdasd")
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@bp.route('/admin/upload', methods=['POST', 'GET'])
@login_required
def upload():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    f = request.files.get('upload')
    if not f:
        return upload_fail(message='No file uploaded.')
    
    extension = f.filename.split('.')[-1].lower()
    if extension not in ['jpg', 'jpeg', 'png', 'gif']:
        return upload_fail(message='Image files only (jpg, jpeg, png, gif).')

    file_path = os.path.join(bp.config['UPLOAD_FOLDER'], f.filename)
    f.save(file_path)

    file_url = url_for('uploaded_files', filename=f.filename)
    return upload_success(file_url, filename=f.filename)

@bp.route('/admin/challenges')
@login_required
def manage_challenges():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    challenges = Challenge.query.order_by(Challenge.date_posted.desc()).all()
    return render_template('admin/manage_challenges.html', title='Manage Challenges', challenges=challenges)

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

# ! USER ROUTES

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
