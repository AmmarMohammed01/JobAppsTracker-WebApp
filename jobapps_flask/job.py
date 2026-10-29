from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from jobapps_flask.auth import login_required
from jobapps_flask.db import get_db

from datetime import datetime

bp = Blueprint('job', __name__)


# should return jobs only for logged in user soon
@bp.route('/')
def index():
    db = get_db()

    jobs = db.execute(
        '''
        SELECT
            j.job_id,
            u.username,
            c.company_name,
            p.platform_name,
            j.job_title,
            r.resume_name,
            s.status_description,
            s.status_datetime,
            w.website_link
        FROM job AS j
        LEFT JOIN user AS u ON u.id = j.user_id
        LEFT JOIN company AS c ON c.company_id = j.company_id
        LEFT JOIN platform AS p ON p.platform_id = j.platform_id
        LEFT JOIN resume AS r ON r.resume_id = j.resume_id
        LEFT JOIN status AS s ON s.job_id = j.job_id
        LEFT JOIN url AS w ON w.job_id = j.job_id
        ORDER BY j.job_id DESC
        '''
    ).fetchall()
    return render_template('job/index.html', jobs=jobs)


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

        # applied_time[10] = ' ' # string are immutable in python, this fails
        # applied_time += ":00"
        applied_time = datetime.fromisoformat(applied_time)
        print(applied_time)  # 2024-09-30 18:49:00

        error = None


        if not title:
            error = 'Title is required.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            # Join the job and company tables based on the company_id
            get_company = db.execute(
                'SELECT company_id, company_name FROM company WHERE company_name = ?', (company,)
            ).fetchone()

            get_resume = db.execute(
                'SELECT resume_id, resume_name FROM resume WHERE resume_name = ?', (resume,)
            ).fetchone()

            get_platform = db.execute(
                'SELECT platform_id, platform_name FROM platform WHERE platform_name = ?', (platform,)
            ).fetchone()

            if get_company is None:
                print("Company not found.")
                cursor = db.execute(
                    '''
                    INSERT INTO company (company_name)
                    VALUES (?)
                    ''',
                    (company,)
                )
                company_id = cursor.lastrowid
                db.commit()
                print(company_id)
                get_company = [company_id]

            if get_resume is None:
                print("Resume not found.")
                cursor = db.execute(
                    '''
                    INSERT INTO resume (resume_name)
                    VALUES (?)
                    ''',
                    (resume,)
                )
                resume_id = cursor.lastrowid
                db.commit()
                print(resume_id)
                get_resume = [resume_id] # get_resume[0] = resume_id is wrong b/c get_resume is NoneType at this point

            if get_platform is None:
                print("Platform not found.")
                cursor = db.execute(
                    '''
                    INSERT INTO platform (platform_name)
                    VALUES (?)
                    ''',
                    (platform,) # in python, parantheses alone don't make a tuple. adding a comma does
                )
                platform_id = cursor.lastrowid
                db.commit()
                print(platform_id)
                get_platform = [platform_id]


            # if, for, while don't have unique scope.
            # functions, classes, comprehensions have unique variable scope

            if get_company and get_resume and get_platform:
                company_id = get_company[0]
                resume_id = get_resume[0]
                platform_id = get_platform[0]
                cursor = db.execute(
                    'INSERT INTO job (user_id, company_id, job_title, resume_id, platform_id)'
                    ' VALUES (?, ?, ?, ?, ?)',
                    (g.user['id'], company_id, title, resume_id, platform_id)
                )
                job_id = cursor.lastrowid
                db.commit()

                db.execute(
                    'INSERT INTO status (job_id, status_datetime, status_description)'
                    'VALUES (?, ?, ?)',
                    (job_id, applied_time, "Applied")
                )
                db.commit()

                db.execute(
                    'INSERT INTO url (job_id, website_link)'
                    'VALUES (?, ?)',
                    (job_id, link)
                )
                db.commit()

                return redirect(url_for('job.index'))

    return render_template('job/create.html')

def get_job(id):
    job = get_db().execute(
        '''
        SELECT
            j.job_title,
            c.company_name,
            p.platform_name,
            r.resume_name
        FROM job AS j
        LEFT JOIN user AS u ON u.id = j.user_id
        LEFT JOIN company AS c ON c.company_id = j.company_id
        LEFT JOIN platform AS p ON p.platform_id = j.platform_id
        LEFT JOIN resume AS r ON r.resume_id = j.resume_id
        WHERE job_id = ?
        ORDER BY j.job_id DESC
        ''',
        (id,)
    ).fetchone()

    if job is None:
        abort(404, f"Job id {id} doesn't exist.")

    return job


@bp.route('/<int:id>/view', methods=('GET',))
@login_required
def view(id):
    job = get_job(id)

    db = get_db()
    statuses = db.execute(
        '''
        SELECT status_description, status_datetime
        FROM status
        WHERE job_id = ?
        ORDER BY status_datetime DESC
        ''',
        (id,)
    ).fetchall()

    links = db.execute(
        '''
        SELECT website_link
        FROM url
        WHERE job_id = ?
        ''',
        (id,)
    ).fetchall()

    return render_template('job/view.html', job=job, statuses=statuses, links=links)

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    job = get_job(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE job SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('job.index'))

    return render_template('job/update.html', job=job)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_job(id)
    db = get_db()
    db.execute('DELETE FROM job WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('job.index'))
