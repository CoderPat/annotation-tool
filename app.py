
from flask import Flask, render_template, request, redirect, url_for

import os 
import db_utils
import sys
from collections import defaultdict

app = Flask(__name__)
app.cli.add_command(db_utils.initdb_command)

IS_RUNNING = 'flask run' in ' '.join(sys.argv)

if IS_RUNNING:
    EXAMPLES_FOLDER = os.path.join('static', 'examples')

    examples_tags = os.listdir(EXAMPLES_FOLDER)
    examples = []
    explanations = defaultdict(list)
    for example_tag in examples_tags:
        example_name, example_prediction = example_tag.split(':')[:2]
        example_path = os.path.join('examples', example_tag, 'image.png')
        examples.append((example_name, example_path, example_prediction))
        for explanation in os.listdir(os.path.join(EXAMPLES_FOLDER, example_tag)):
            if explanation.endswith('.png') and explanation != 'image.png':
                explanation_name = explanation[:-4]
                explanation_path = os.path.join('examples', example_tag, explanation)
                explanations[example_name].append((explanation_name, explanation_path))

    with app.app_context():
        db_utils.check_and_update_examples(examples, explanations)

    @app.route('/', methods=['GET', 'POST'])
    def index():
        db = db_utils.get_db()
        cursor = db.cursor()
        if request.method == 'POST':
            username = request.form['username']
            userid = db_utils.get_userid(username)
            if request.form['action'] == 'register':
                if userid is not None:
                    return redirect(url_for('index', error='User already exists'))
                else:
                    cursor.execute(
                        "INSERT INTO users (username) VALUES (?)",
                        (username,)
                    )
                    db.commit()
                    return redirect(url_for('dashboard', name=username))
            elif request.form['action'] == 'login':
                if userid is None:
                    return redirect(url_for('index', error='User does not exist'))
                else:
                    return redirect(url_for('dashboard', name=username))

        return render_template('index.html', examples=examples, error=request.args.get('error'))

    @app.route('/dashboard', methods=['GET'])
    def dashboard():
        userid = db_utils.get_userid(request.args['name'])
        example_ids = db_utils.get_example_ids()
        example_ids = sorted(example_ids)
        explanations = db_utils.get_explanations()
        explanations_evaluations = db_utils.get_explanations_evaluations(userid)

        counts = defaultdict(int)
        for example_id in example_ids:
            for explanation in explanations:
                for evaluation in explanations_evaluations:
                    if explanation[1] == example_id and explanation[0] == evaluation[1]:
                        counts[example_id] += 1


        return render_template(
            'dashboard.html', 
            name=request.args.get('name'),
            examples=[{"id": example_id, "count": counts[example_id]} for example_id in example_ids]
        )

    @app.route('/example', methods=['GET', 'POST'])	
    def example():
        userid = db_utils.get_userid(request.args['name'])
        example_id = request.args['example_id']
        example = db_utils.get_example(example_id)
        explanations = db_utils.get_explanations(example_id)

        if request.method == 'POST':
            for explananation in explanations:
                score = request.form.get(f"score_{explananation['id']}")
                if score != "":
                    db_utils.update_explanation_evaluation(userid, explananation['id'], score)
        
        explanations_evaluations = db_utils.get_explanations_evaluations(userid)

        scores = defaultdict(str)
        for explanation in explanations:
            for evaluation in explanations_evaluations:
                if explanation[0] == evaluation[1]:
                    scores[explanation[0]] = evaluation['score']

        return render_template(
            "example.html", 
            name=request.args.get('name'), 
            example={
                "id": int(example_id),
                "path": example[2],
                "prediction": example[3]
            },
            explanations=[
                {
                    "id": explanation[0],
                    "path": explanation[3], 
                    "score": scores[explanation[0]] 
                }
                for explanation in explanations 
            ]
        )