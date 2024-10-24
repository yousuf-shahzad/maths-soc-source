import os, datetime
from werkzeug.utils import secure_filename
from io import BytesIO
from flask import render_template, flash, redirect, url_for, request, send_from_directory, current_app, send_file
from flask_login import login_required, current_user
from flask_ckeditor import upload_success, upload_fail
from app import db
from app.admin import bp
from app.models import Article, Challenge, User, AnswerSubmission
from app.admin.forms import ChallengeForm, ArticleForm, AnswerSubmissionForm

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
        article = Article(
            title=form.title.data,
            content=form.content.data,
            named_creator=form.author.data,
            user_id=current_user.id,
            type=form.type.data,
            date_posted = datetime.datetime.now(),
        )
        
        if form.type.data == 'newsletter' and form.file.data:
            # Create newsletters directory if it doesn't exist
            print(form.file.data)
            newsletter_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'newsletters')
            os.makedirs(newsletter_path, exist_ok=True)
            
            # Save PDF file
            checking_id = article.date_posted.strftime('%Y_%m')
            filename = secure_filename(f"newsletter_{checking_id}_{form.file.data.filename}")
            file_path = os.path.join(newsletter_path, filename)
            form.file.data.save(file_path)
            article.file_url = filename

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

# In admin/routes.py

@bp.route('/admin/articles/edit/<int:article_id>', methods=['GET', 'POST'])
@login_required
def edit_article(article_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    
    article = Article.query.get_or_404(article_id)
    form = ArticleForm(obj=article)

    if form.validate_on_submit():
        article.title = form.title.data
        article.content = form.content.data
        article.named_creator = form.author.data
        article.type = form.type.data
        
        if form.type.data == 'newsletter' and form.file.data:
            # Create newsletters directory if it doesn't exist
            newsletter_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'newsletters')
            os.makedirs(newsletter_path, exist_ok=True)
            
            # Delete old file if it exists
            if article.file_url:
                old_file_path = os.path.join(newsletter_path, article.file_url)
                try:
                    os.remove(old_file_path)
                except OSError:
                    pass
            
            # Save new PDF file
            filename = secure_filename(f"newsletter_{article.date_posted.strftime('%Y_%m')}_{form.file.data.filename}")
            file_path = os.path.join(newsletter_path, filename)
            form.file.data.save(file_path)
            article.file_url = filename
        
        db.session.commit()
        flash(f'{article.type.capitalize()} updated successfully.')
        return redirect(url_for('admin.manage_articles'))
    
    # Pre-populate the form
    form.title.data = article.title
    form.content.data = article.content
    form.author.data = article.named_creator
    form.type.data = article.type
    
    return render_template('admin/edit_article.html', 
                         title=f'Edit {article.type.capitalize()}', 
                         form=form, 
                         article=article)

@bp.route('/admin/articles/delete/<int:article_id>')
@login_required
def delete_article(article_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    
    article = Article.query.get_or_404(article_id)
    
    # Delete associated PDF file if it exists
    if article.type == 'newsletter' and article.file_url:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 
                                'newsletters', 
                                article.file_url)
        try:
            os.remove(file_path)
        except OSError:
            current_app.logger.warning(f"Could not delete file: {file_path}")
    
    db.session.delete(article)
    db.session.commit()
    
    flash(f'{article.type.capitalize()} deleted successfully.')
    return redirect(url_for('admin.manage_articles'))

# ! CHALLENGE ROUTES

def create_challenge_folder(create_date):
    create_date = create_date.strftime('%Y-%m-%d')
    print(create_date)
    challenge_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f'challenge_{create_date}')
    challenge_responses = os.path.join(challenge_path, 'responses/')
    os.makedirs(os.path.dirname(challenge_responses), exist_ok=True)
    return challenge_path

# Modified route handler
@bp.route('/challenges/<int:challenge_id>', methods=['GET', 'POST'])
@login_required
def view_challenge(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    form = AnswerSubmissionForm()
    
    if form.validate_on_submit():
        submission = AnswerSubmission(
            user_id=current_user.id,
            challenge_id=challenge.id,
            answer=form.answer.data
        )
        
        try:
            db.session.add(submission)
            db.session.commit()
            
            is_correct = form.answer.data.lower().strip() == challenge.correct_answer.lower().strip()
            flash(f'Your answer is {"correct" if is_correct else "incorrect"}!',
                  'success' if is_correct else 'error')
                  
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error: {str(e)}")
            flash('Error submitting answer. Please try again.', 'error')
        
        return redirect(url_for('admin.view_challenge', challenge_id=challenge_id))
    
    # Get previous submissions for this user and challenge
    previous_submission = AnswerSubmission.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id
    ).first()
    
    if previous_submission:
        form.answer.data = previous_submission.answer
    
    return render_template('admin/challenge.html', 
                         title=challenge.title,
                         challenge=challenge,
                         form=form)

@bp.route('/admin/challenges/create', methods=['GET', 'POST'])
@login_required
def create_challenge():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('main.index'))

    form = ChallengeForm()
    if form.validate_on_submit():
        try:
            challenge = Challenge(
                title=form.title.data,
                content=form.content.data,
                date_posted=datetime.datetime.now(),
                key_stage=form.key_stage.data,
                correct_answer=form.correct_answer.data
            )
            
            challenge_folder = create_challenge_folder(challenge.date_posted)
            if form.image.data:
                try:
                    filename = secure_filename(form.image.data.filename)
                    file_path = os.path.join(challenge_folder, filename)
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
        challenge.key_stage = form.key_stage.data
        challenge.correct_answer = form.correct_answer.data
        
        if form.image.data:
            try:
                challenge_folder = create_challenge_folder(challenge.date_posted)
                filename = secure_filename(form.image.data.filename)
                file_path = os.path.join(challenge_folder, filename)
                form.image.data.save(file_path)
                challenge.file_url = filename
            except IOError as e:
                current_app.logger.error(f"File save error: {str(e)}")
                flash('Error saving the image file. Please try again.', 'error')
                return render_template('admin/edit_challenge.html', title='Edit Challenge', form=form)
        
        db.session.commit()
        flash('Challenge updated successfully.')
        return redirect(url_for('admin.manage_challenges'))
    
    # Pre-populate the form
    form.title.data = challenge.title
    form.content.data = challenge.content
    form.key_stage.data = challenge.key_stage
    form.correct_answer.data = challenge.correct_answer
    if challenge.file_url:
        post_date = challenge.date_posted.strftime('%Y-%m-%d')
        form.file_url = f'challenge_{post_date}/{challenge.file_url}'
        
    return render_template('admin/edit_challenge.html', title='Edit Challenge', form=form)

@bp.route('/static/uploads/<path:id>')
def uploaded_files(id):
    challenge = Challenge.query.get_or_404(id)
    date_posted = challenge.date_posted.strftime('%Y-%m-%d')
    filename = challenge.file_url
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], f'challenge_{date_posted}/{filename}')

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
    
@bp.route('/admin/challenges/delete/<int:challenge_id>')
@login_required
def delete_challenge(challenge_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    
    challenge = Challenge.query.get_or_404(challenge_id)

    try:
        filename = challenge.file_url
        os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
    except:
        pass

    try:
        date_posted = challenge.date_posted.strftime('%Y-%m-%d')
        os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], f'challenge_{date_posted}/responses/'))
    except:
        pass

    submissions = AnswerSubmission.query.filter_by(challenge_id=challenge_id).all()
    for submission in submissions:
        db.session.delete(submission)

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
