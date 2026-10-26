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
    '''
    'SELECT job_id, user_id, company_id, platform_id, job_title, resume_id'
    ' FROM job'
    '''
    jobs = db.execute(
        '''
        SELECT
            j.job_id,
            u.username,
            c.company_name,
            p.platform_name,
            j.job_title,
            r.resume_name
        FROM job AS j
        LEFT JOIN user AS u ON u.id = j.user_id
        LEFT JOIN company AS c ON c.company_id = j.company_id
        LEFT JOIN platform AS p ON p.platform_id = j.platform_id
        LEFT JOIN resume AS r ON r.resume_id = j.resume_id
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
                db.execute(
                    'INSERT INTO job (user_id, company_id, job_title, resume_id, platform_id)'
                    ' VALUES (?, ?, ?, ?, ?)',
                    (g.user['id'], company_id, title, resume_id, platform_id)
                )
                db.commit()
                return redirect(url_for('job.index'))

    return render_template('job/add.html')