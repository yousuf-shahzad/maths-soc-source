"""
Main Routes Module
==================

This module handles all the main user-facing routes.
It is organized into logical sections based on functionality:
- View Routes
- Challenge Routes
- Article and Newsletter Routes
- Leaderboard Routes

Dependencies:
------------
- Flask and related extensions
- SQLAlchemy for database operations
- Custom models and forms using Flask-WTF

Security:
---------
User authentication and registration are handled securely:
1. All sensitive routes require authentication
2. File access is properly sanitized
3. User permissions are checked appropriately
4. Form data is validated before processing

Maintenance Notes:
-----------------
1. Ensure that the database schema is up-to-date with the models.
2. Validate form data before processing it in routes.
3. Keep the user experience simple and user-friendly.
4. Handle errors gracefully and provide helpful messages.
"""

import os
from flask import (
    abort,
    current_app,
    render_template,
    flash,
    redirect,
    send_from_directory,
    url_for,
    request,
)
from flask_login import current_user
import datetime
from typing import Dict
from app import db
from app.models import User
from sqlalchemy.exc import SQLAlchemyError
from app.main import bp
from app.models import (
    Challenge,
    Article,
    LeaderboardEntry,
    AnswerSubmission,
    ChallengeAnswerBox,
    Announcement,
)
from app.admin.forms import AnswerSubmissionForm


# ============================================================================
# View Routes
# ============================================================================


@bp.route("/")
@bp.route("/home")
def home():
    """
    Render the homepage with recent content.

    Returns:
        Rendered homepage template with recent challenges, articles, leaderboard entries,
        latest newsletter, and latest announcement.

    Notes:
        - Displays most recent challenges and articles (limited to 3 each)
        - Shows the latest newsletter and announcement
        - Falls back to the about page if a database error occurs
    """
    try:
        challenges = Challenge.query
        articles = Article.query
        leaderboard_entries = LeaderboardEntry.query
        recent_challenges = (
            Challenge.query.order_by(Challenge.date_posted.desc()).limit(3).all()
        )

        recent_articles = (
            Article.query.filter_by(type="article")
            .order_by(Article.date_posted.desc())
            .limit(3)
            .all()
        )

        latest_newsletter = (
            Article.query.filter_by(type="newsletter")
            .order_by(Article.date_posted.desc())
            .first()
        )

        latest_announcement = Announcement.query.order_by(
            Announcement.date_posted.desc()
        ).first()

        return render_template(
            "index.html",
            challenges=challenges,
            articles=articles,
            leaderboard_entries=leaderboard_entries,
            recent_challenges=recent_challenges,
            recent_articles=recent_articles,
            latest_newsletter=latest_newsletter,
            latest_announcement=latest_announcement,
        )
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in index route: {str(e)}")
        flash("An error occurred while loading the homepage.", "error")
        return redirect(url_for("main.about"))


@bp.route("/about")
def about():
    """
    Render the about page.

    Returns:
        Rendered about page template.
    """
    return render_template("main/about.html", title="About")


# ============================================================================
# Challenge Routes
# ============================================================================


@bp.route("/challenges")
def challenges():
    """
    List all challenges with pagination.

    Query Parameters:
        page (int, optional): Current page number for pagination. Defaults to 1.

    Returns:
        Rendered challenges page template with paginated challenges.

    Notes:
        - Displays 6 challenges per page
        - Sorted by most recent date posted
        - Redirects to index if database error occurs
    """
    page = request.args.get("page", 1, type=int)
    try:
        challenges_pagination = Challenge.query.order_by(
            Challenge.date_posted.desc()
        ).paginate(page=page, per_page=6, error_out=False)

        return render_template("main/challenges.html", challenges=challenges_pagination)
    except SQLAlchemyError as e:
        current_app.logger.error(f"Error loading challenges: {str(e)}")
        flash("Unable to load challenges at this time.", "error")
        return redirect(url_for("main.home"))


def check_submission_count(user_id: int, challenge_id: int, box_id: int) -> int:
    """
    Check how many submissions a user has made for a specific answer box.

    Args:
        user_id (int): The ID of the user.
        challenge_id (int): The ID of the challenge.
        box_id (int): The ID of the answer box.

    Returns:
        int: Number of submissions for the specified user, challenge, and answer box.
    """
    return AnswerSubmission.query.filter_by(
        user_id=user_id, challenge_id=challenge_id, answer_box_id=box_id
    ).count()


def create_submission(
    user_id: int,
    challenge_id: int,
    answer_box: ChallengeAnswerBox,
    submitted_answer: str,
) -> AnswerSubmission:
    """
    Create and save a new submission.

    Args:
        user_id (int): The ID of the user.
        challenge_id (int): The ID of the challenge.
        answer_box (ChallengeAnswerBox): The answer box object.
        submitted_answer (str): The user's submitted answer.

    Returns:
        AnswerSubmission: Created submission object.
    """
    submission = AnswerSubmission(
        user_id=user_id,
        challenge_id=challenge_id,
        answer_box_id=answer_box.id,
        answer=submitted_answer,
        is_correct=submitted_answer.lower().strip()
        == answer_box.correct_answer.lower().strip(),
    )

    db.session.add(submission)
    db.session.commit()
    return submission


def check_all_answers_correct(challenge: Challenge, user_id: int) -> bool:
    """
    Check if user has correct submissions for all answer boxes in a challenge.

    Args:
        challenge (Challenge): The Challenge object.
        user_id (int): The ID of the user.

    Returns:
        bool: True if all answers are correct, False otherwise.
    """
    return all(
        AnswerSubmission.query.filter_by(
            user_id=user_id,
            challenge_id=challenge.id,
            answer_box_id=box.id,
            is_correct=True,
        ).first()
        is not None
        for box in challenge.answer_boxes
    )


def update_leaderboard(user_id: int, score: int, challenge_key_stage: str) -> None:
    """
    Update user's points on the leaderboard for the specific challenge key stage.

    Args:
        user_id (int): The ID of the user.
        score (int): Number of points to add.
        challenge_key_stage (str): The key stage of the challenge being completed.
    """

    user = User.query.get(user_id)
    if not user:
        return
    
    # Look for existing leaderboard entry for this user and challenge key stage
    leaderboard_entry = LeaderboardEntry.query.filter_by(
        user_id=user_id, 
        key_stage=challenge_key_stage
    ).first()

    if leaderboard_entry:
        leaderboard_entry.score += score
    else:
        # Create new entry for this key stage
        leaderboard_entry = LeaderboardEntry(
            user_id=user_id, 
            score=score, 
            key_stage=challenge_key_stage
        )
        db.session.add(leaderboard_entry)

    leaderboard_entry.last_updated = datetime.datetime.utcnow()
    db.session.commit()


def handle_submission_result(
    submission: AnswerSubmission, challenge: Challenge, answer_box: ChallengeAnswerBox
) -> None:
    """
    Handle the result of a submission, updating points and showing appropriate messages.

    Args:
        submission (AnswerSubmission): The AnswerSubmission object.
        challenge (Challenge): The Challenge object.
        answer_box (ChallengeAnswerBox): The ChallengeAnswerBox object.

    Notes:
        - Flashes success message for correct answers
        - Awards bonus points for first correct solution
        - Tracks remaining attempts for incorrect answers
        - Updates leaderboard based on challenge key stage, not user key stage
    """
    submission_count = check_submission_count(
        submission.user_id, challenge.id, answer_box.id
    )

    if submission.is_correct:
        flash(f"Correct answer for {answer_box.box_label}!", "success")

        # Check if all parts are now correct
        if check_all_answers_correct(challenge, submission.user_id):
            # Award bonus points for first correct solution
            if challenge.first_correct_submission is None:
                challenge.first_correct_submission = datetime.datetime.utcnow()
                # First solution bonus - use challenge's key stage
                update_leaderboard(submission.user_id, 3, challenge.key_stage)
            else:
                # Regular completion points - use challenge's key stage
                update_leaderboard(submission.user_id, 1, challenge.key_stage)

            db.session.commit()
    else:
        remaining = 3 - submission_count
        flash(
            f"Incorrect answer for {answer_box.box_label}. {remaining} attempts remaining.",
            "error",
        )

@bp.route("/challenges/<int:challenge_id>", methods=["GET", "POST"])
def challenge(challenge_id: int):
    """
    Display a specific challenge and handle answer submissions.

    Args:
        challenge_id (int): The ID of the challenge to display.

    Returns:
        Rendered challenge template with submission forms and previous submissions.

    Notes:
        - Requires user authentication to submit answers
        - Tracks remaining attempts and previous submissions
        - Prevents submission after maximum attempts are reached
    """
    challenge = Challenge.query.get_or_404(challenge_id)
    forms = {}
    submissions = {}

    # Create forms and get submissions only if user is authenticated
    if current_user.is_authenticated:
        for answer_box in challenge.answer_boxes:
            forms[answer_box.id] = AnswerSubmissionForm()
            submissions[answer_box.id] = (
                AnswerSubmission.query.filter_by(
                    user_id=current_user.id,
                    challenge_id=challenge_id,
                    answer_box_id=answer_box.id,
                )
                .order_by(AnswerSubmission.submitted_at.desc())
                .all()
            )

        # Handle submission if the form is submitted
        if request.method == "POST":
            return handle_challenge_submission(challenge, forms)

    all_correct = current_user.is_authenticated and check_all_answers_correct(
        challenge, current_user.id
    )

    return render_template(
        "main/challenge.html",
        challenge=challenge,
        forms=forms if current_user.is_authenticated else None,
        submissions=submissions,
        attempts_remaining=3,
        all_correct=all_correct,
    )


def handle_challenge_submission(challenge: Challenge, forms: Dict) -> redirect:
    """
    Process a challenge submission.

    Args:
        challenge (Challenge): The Challenge object.
        forms (Dict): Dictionary of forms for each answer box.

    Returns:
        Redirect: Response redirecting back to the challenge page.

    Notes:
        - Validates form submission
        - Checks remaining attempts
        - Creates and handles submission result
    """
    box_id = int(request.form.get("answer_box_id"))
    form = forms[box_id]

    if not form.validate_on_submit():
        flash("Invalid submission.", "error")
        return redirect(url_for("main.challenge", challenge_id=challenge.id))

    answer_box = ChallengeAnswerBox.query.get_or_404(box_id)
    submission_count = check_submission_count(current_user.id, challenge.id, box_id)

    if submission_count >= 3 and not has_correct_submission(
        current_user.id, challenge.id
    ):
        flash("You have reached the maximum attempts for this part.", "error")
        return redirect(url_for("main.challenge", challenge_id=challenge.id))

    submission = create_submission(
        current_user.id, challenge.id, answer_box, form.answer.data
    )

    handle_submission_result(submission, challenge, answer_box)
    return redirect(url_for("main.challenge", challenge_id=challenge.id))


@bp.route("/articles")
def articles():
    """
    List all articles.

    Returns:
        Rendered articles page template with all articles sorted by most recent.
    """
    articles = (
        Article.query.filter_by(type="article")
        .order_by(Article.date_posted.desc())
        .all()
    )
    return render_template("main/articles.html", title="Articles", articles=articles)


@bp.route("/newsletters/<path:filename>")
def serve_newsletter(filename):
    """
    Serve a newsletter file from the uploads directory.

    Args:
        filename (str): Name of the newsletter file to serve.

    Returns:
        Sent newsletter file from the uploads directory.
    """
    return send_from_directory(
        os.path.join(current_app.config["UPLOAD_FOLDER"], "newsletters"), filename
    )


def check_user_submission_count(user_id, challenge_id):
    """
    Check the total number of submissions for a user in a specific challenge.

    Args:
        user_id: The ID of the user.
        challenge_id: The ID of the challenge.

    Returns:
        int: Total number of submissions for the user in the challenge.
    """
    return AnswerSubmission.query.filter_by(
        user_id=user_id, challenge_id=challenge_id
    ).count()


def has_correct_submission(user_id, challenge_id):
    """
    Check if a user has a correct submission for a specific challenge.

    Args:
        user_id: The ID of the user.
        challenge_id: The ID of the challenge.

    Returns:
        bool: True if the user has a correct submission, False otherwise.
    """
    return (
        AnswerSubmission.query.filter_by(
            user_id=user_id, challenge_id=challenge_id, is_correct=True
        ).first()
        is not None
    )


@bp.route("/newsletters")
def newsletters():
    """
    List all newsletters.

    Returns:
        Rendered newsletters page template with all newsletters sorted by most recent.
    """
    newsletters = (
        Article.query.filter_by(type="newsletter")
        .order_by(Article.date_posted.desc())
        .all()
    )
    return render_template(
        "main/newsletters.html", title="Newsletters", articles=newsletters
    )


@bp.route("/newsletter/<int:id>")
def newsletter(id):
    """
    Display a specific newsletter.

    Args:
        id (int): The ID of the newsletter.

    Returns:
        Rendered newsletter detail page.

    Raises:
        404 Error: If the article is not a newsletter.
    """
    article = Article.query.get_or_404(id)
    if article.type != "newsletter":
        abort(404)
    return render_template("main/newsletter.html", article=article)


@bp.route("/article/<int:id>")
def article(id):
    """
    Display a specific article.

    Args:
        id (int): The ID of the article.

    Returns:
        Rendered article detail page.

    Raises:
        404 Error: If the article is not an article type.
    """
    article = Article.query.get_or_404(id)
    if article.type != "article":
        abort(404)
    return render_template("main/article.html", title=article.title, article=article)


@bp.route("/leaderboard")
def leaderboard():
    """
    Display leaderboards separated by key stages.

    Returns:
        Rendered leaderboard page with entries grouped by key stage.
        
    Notes:
        - Now filters by LeaderboardEntry.key_stage instead of User.key_stage
        - This shows scores based on challenge difficulty completed, not user's year group
        - Users may appear on multiple leaderboards if they completed challenges from different key stages
    """
    ks3_entries = (
        LeaderboardEntry.query.join(User)
        .filter(LeaderboardEntry.key_stage == 'KS3')
        .order_by(LeaderboardEntry.score.desc())
        .limit(10)
        .all()
    )
    
    ks4_entries = (
        LeaderboardEntry.query.join(User)
        .filter(LeaderboardEntry.key_stage == 'KS4')
        .order_by(LeaderboardEntry.score.desc())
        .limit(10)
        .all()
    )
    
    ks5_entries = (
        LeaderboardEntry.query.join(User)
        .filter(LeaderboardEntry.key_stage == 'KS5')
        .order_by(LeaderboardEntry.score.desc())
        .limit(10)
        .all()
    )
    
    return render_template(
        "main/leaderboard.html", 
        title="Leaderboards",
        ks3_entries=ks3_entries,
        ks4_entries=ks4_entries,
        ks5_entries=ks5_entries
    )


@bp.route("/privacy_policy")
def privacy_policy():
    """
    Display the privacy policy.

    Returns:
        Rendered privacy policy page.
    """
    return render_template(
        "main/privacy_policy.html",
        title="Privacy Policy",
        current_date=datetime.datetime.utcnow(),
    )
