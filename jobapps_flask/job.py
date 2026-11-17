from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from jobapps_flask.auth import login_required
from jobapps_flask.db import get_db

from datetime import datetime

bp = Blueprint('job', __name__, url_prefix='/jobs')


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
            MAX(s.status_datetime) as latest_status_time,
            w.website_link
        FROM job AS j
        LEFT JOIN user AS u ON u.id = j.user_id
        LEFT JOIN company AS c ON c.company_id = j.company_id
        LEFT JOIN platform AS p ON p.platform_id = j.platform_id
        LEFT JOIN resume AS r ON r.resume_id = j.resume_id
        LEFT JOIN status AS s ON s.job_id = j.job_id
        LEFT JOIN url AS w ON w.job_id = j.job_id
        WHERE u.id = ?
        GROUP BY j.job_id
        ORDER BY latest_status_time DESC
        ''',
        (g.user['id'],)
    ).fetchall() # could have also done ORDER BY MAX(s.status_datetime)

    job_count_this_week = db.execute(
        '''
        SELECT count(S.job_id) as current_week_job_count
        FROM status as S, job as J
        WHERE
            S.status_description = 'Applied'
            AND
            S.status_datetime >= date('now', 'weekday 0', '-7 days')
            AND
            S.status_datetime < date('now', 'weekday 0')
            AND
            S.job_id = J.job_id
            AND
            J.user_id = ?;
        ''',
        (g.user['id'],)
    ).fetchone()

    return render_template('job/view_all.html', jobs=jobs, job_count_this_week=job_count_this_week)


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
                    INSERT INTO resume (resume_name, user_id)
                    VALUES (?, ?)
                    ''',
                    (resume, g.user['id'])
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
            j.job_id,
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
    j = get_job(id)

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

    # add KeyError, if job index that doesn't exist is called

    return render_template('job/view.html', j=j, statuses=statuses, links=links)

@bp.route('/<int:id>/status/add', methods=('POST',))
@login_required
def add_status(id):
    # how to get these variables? These are user inputs from frontend
    # I should have input box, perhaps in form tag, to obtain request.
    if request.method == "POST":
        status_datetime = request.form['status_datetime']
        status_description = request.form['status_description']

        status_datetime = datetime.fromisoformat(status_datetime)

        print(id)
        # print(request.form['id'])
        print(status_description)
        print(status_datetime)

        # check if correct user is calling endpoint
        db = get_db()
        db.execute(
            '''
            INSERT INTO status (job_id, status_datetime, status_description)
            VALUES (?, ?, ?)
            ''',
            (id, status_datetime, status_description)
        )
        db.commit()
        return redirect(url_for('job.view', id=id))


@bp.route('/<int:id>/url/add', methods=('POST',))
@login_required
def add_url(id):
    if request.method == "POST":
        website_link = request.form['website_link']

        db = get_db()
        db.execute(
            '''
            INSERT INTO url (job_id, website_link)
            VALUES (?, ?)
            ''',
            (id, website_link)
        )
        db.commit()
        return redirect(url_for('job.view', id=id))

# is any user able to delete? only user creating the job should delete
# currently when job is deleted, a bunch of information remains: url, resume, company
@bp.route('/<int:id>', methods=('DELETE',))
@login_required
def delete(id):
    get_job(id)
    db = get_db()
    db.execute('DELETE FROM job WHERE job_id = ?', (id,))
    db.commit()
    # return redirect(url_for('job.index'))
    return "", 204
