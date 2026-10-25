from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from jobapps_flask.auth import login_required
from jobapps_flask.db import get_db


bp = Blueprint('job', __name__)


@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT job_id, user_id, company_id, platform_id, job_title, resume_id'
        ' FROM job'
    ).fetchall()
    return render_template('job/index.html')


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        company = request.form['company']
        title = request.form['job']
        link = request.form['link']
        applied_time = request.form['applied_time']
        resume = request.form['resume']
        platform = request.form['platform']
        error = None

        """
        if not title:
            error = 'Title is required.'
        """

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('job.index'))

    return render_template('job/add.html')