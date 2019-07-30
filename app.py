from flask import Flask, jsonify, request, abort, redirect, render_template
from helpers import (x_input, text_processor, code_lookup, code_descriptions, load_model, response_description, top_n_probabilities)
from time import time
from flask_cors import cross_origin

DRUG_SECTIONS = ["IN01", "LS01", "PYROT", "STYOT", "SVYOT", "TRYOT", "SD02", "SD15", "TX21", "TX36"]

# Load model into memory
model = load_model()

class CustomFlask(Flask):
    jinja_options = Flask.jinja_options.copy()
    jinja_options.update(dict(
        variable_start_string='%%',  # Default is '{{', I'm changing this because Vue.js uses '{{' / '}}'
        variable_end_string='%%',
    ))


app = CustomFlask(__name__)

@app.route('/')
def index():
    return redirect('/interface/')

@app.route('/interface/')
@cross_origin(allow_headers=['*'])
def interface():
    return render_template('interface.html')

@app.route('/api/')
def api():
    return render_template('api.html')

@app.route('/drug-predict/', methods=['POST'])
@cross_origin(allow_headers=['*'])
def course_predict():
    start_time = time()
    if request.is_json is True:
        request_type = "json"
        request_data = request.get_json()
    else:
        request_type = "form"
        request_data = request.form

    no_drug_type = not 'drug_section' in request_data
    no_drug_text = not 'drug_text' in request_data
    if not request_data or (no_drug_type or no_drug_text):
        bad_request_response = {'error' : 'Data missing drug_section or drug_text variables', 'request_type': request_type}
        return jsonify(bad_request_response)

    # Get number of predictions to return
    if 'prediction_count' not in request_data:
        top_n = 10
    else:
        top_n = request_data['prediction_count']

    drug_section = request_data['drug_section']
    drug_text = request_data['drug_text']

    # Make sure drug section is an actual drug section
    if drug_section not in DRUG_SECTIONS:
        bad_request_response = {'error': 'Drug section must be one of the following: {0}'.format(", ".join(DRUG_SECTIONS))}
        return jsonify(bad_request_response)

    processed_input = x_input(drug_section, drug_text)
    tokenized_input = text_processor.process([processed_input])

    predictions = model.predict_proba(tokenized_input) # probability for every y
    sorted_pred_idx = [top_n_probabilities(p,top_n) for p in predictions][0] # sorted indices
    drug_codes = [code_lookup[code] for code in sorted_pred_idx]
    p_values = [float(predictions[0][idx]) for idx in sorted_pred_idx]
    predicted_codes = zip(sorted_pred_idx, drug_codes,p_values)

    predictions_formatted = []
    for i, (code_id, code, p) in enumerate(predicted_codes):
        p_fmt = {'sc_code': code,
                'code_id': int(code_id),
                'code_definition': code_descriptions.get(code, "Unknown code"),
                'p': p,
                'p_rank' : i + 1}
        predictions_formatted.append(p_fmt)
    submitted_data =  {'drug_section': drug_section,'drug_text': drug_text,'prediction_count':top_n}

    warning = None

    if max(pred['p'] for pred in predictions_formatted) <= 0.4:
        warning = "Max prediction less than 0.4, model is uncertain about this course prediction"

    time_elapsed = time() - start_time

    info = {
        'warning' : warning,
        'time_elapsed' : str(round(time_elapsed, 2)) + ' s',
    }

    response = {
        'description' : response_description,
        'submitted_data' : submitted_data,
        'info' : info,
        'predictions': predictions_formatted
    }

    return jsonify(response)
