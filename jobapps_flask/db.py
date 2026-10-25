import sqlite3
from datetime import datetime

import click
from flask import current_app, g


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()

    # open_resource() opens file relative to flaskr package
    with current_app.open_resource('jobapps_sqlite.sql') as f:
        db.executescript(f.read().decode('utf8'))


# defines command line command called init-db
# flask --app flaskr init-db --> OUTPUT: `Initialized the database.`
@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


sqlite3.register_converter(
    # how to interpret timestamp, we will use datetime.datetime
    "timestamp", lambda v: datetime.fromisoformat(v.decode())
)


def init_app(app):
    app.teardown_appcontext(close_db) # function called when cleaning up after returning a response
    app.cli.add_command(init_db_command) # adds new command that can be use w/ `flask` command
