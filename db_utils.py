import sqlite3
from flask import current_app, g, cli
import click
import random
import pandas

DATABASE = './database.db'


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            DATABASE,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


@click.command('initdb')
@cli.with_appcontext
def initdb_command():
    """Initializes the database."""
    db = get_db()
    with current_app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    print('Initialized the database.')


@click.command('dumpevals')
@click.argument('filename')
@cli.with_appcontext
def dumpevals_command(filename):
    """Initializes the database."""
    db = get_db()
    df = pandas.read_sql_query(
        "SELECT explanations_evaluation.id, name, example_id, username, score "
        "FROM explanations_evaluation "
        "INNER JOIN explanations ON explanations_evaluation.explanation_id = explanations.id "
        "INNER JOIN users ON explanations_evaluation.user_id = users.id",
        db
    )
    df.to_csv(filename, index=False, header=True)
    db.commit()
    print('Dumped database.')


def get_userid(username):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT id FROM users WHERE username = ?",
        (username,)
    )
    userid = cursor.fetchone()
    return userid[0] if userid else None

def get_example_ids():
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT id FROM examples"
    )
    return [row[0] for row in cursor.fetchall()]


def get_example(example_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT * FROM examples WHERE id = ?",
        (example_id,)
    )
    return cursor.fetchone()

def get_explanations(example_id=None):
    db = get_db()
    cursor = db.cursor()
    if example_id:
        cursor.execute(
            "SELECT * FROM explanations WHERE example_id = ?",
            (example_id,)
        )
    else:
        cursor.execute(
            "SELECT * FROM explanations"
        )
    return cursor.fetchall()

def get_explanations_evaluations(userid):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT * FROM explanations_evaluation WHERE user_id = ?",
        (userid,)
    )
    return cursor.fetchall()

def update_explanation_evaluation(userid, explanation_id, score):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT * FROM explanations_evaluation WHERE user_id = ? AND explanation_id = ?",
        (userid, explanation_id)
    )
    existing_evaluation = cursor.fetchone()
    if existing_evaluation:
        cursor.execute(
            "UPDATE explanations_evaluation SET score = ? WHERE user_id = ? AND explanation_id = ?",
            (score, userid, explanation_id)
        )
    else:
        cursor.execute(
            "INSERT INTO explanations_evaluation (user_id, explanation_id, score) VALUES (?, ?, ?)",
            (userid, explanation_id, score)
        )
    db.commit()

def check_and_update_examples(examples, explanations, randomize_explanations=True):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT * FROM examples"
    )
    existing_examples = cursor.fetchall()
    existing_examples = {example['name']: example for example in existing_examples}
    for example_name, example_path, example_prediction in examples:
        if example_name not in existing_examples:
            print(f"adding new example: {example_name}")
            if not explanations[example_name]:
                print(f"no explanations for example: {example_name}")
                print("skipping example")
                continue
            
            cursor.execute(
                "INSERT INTO examples (name, path, prediction) VALUES (?, ?, ?)",
                (example_name, example_path, example_prediction)
            )

            example_id = cursor.lastrowid
            example_explanations = explanations[example_name]
            if randomize_explanations:
                random.shuffle(example_explanations)
            for explanation_name, explanation_path in example_explanations:
                cursor.execute(
                    "INSERT INTO explanations (example_id, name, path) VALUES (?, ?, ?)",
                    (example_id, explanation_name, explanation_path)
                )
        else:
            example_id = existing_examples[example_name]['id']
            cursor.execute(
                "SELECT * FROM explanations WHERE example_id = ?",
                (example_id,)
            )
            existing_explanations = cursor.fetchall()
            if not existing_explanations:
                raise Exception(f"no explanations for example: {example}")

            if set(explanations[example_name]) != set((expl["name"], expl["path"]) for expl in existing_explanations):
                print(f"updating example: {example_name}")
                cursor.execute(
                    "DELETE FROM explanations WHERE example_id = ?",
                    (example_id,)
                )
            
                example_explanations = explanations[example_name]
                if randomize_explanations:
                    random.shuffle(example_explanations)
                for explanation_name, explanation_path in example_explanations:
                    cursor.execute(
                        "INSERT INTO explanations (example_id, name, path) VALUES (?, ?, ?)",
                        (example_id, explanation_name, explanation_path)
                    )

        db.commit()

                
            
            
                