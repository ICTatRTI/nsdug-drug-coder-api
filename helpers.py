from pathlib import Path
import json
from sklearn.externals import joblib
from keras.models import model_from_json
import numpy as np
from keras.preprocessing import sequence
from SPARQLWrapper import SPARQLWrapper, JSON

# Set parameters:
model_path = Path('./model/')

# Set parameters
with open(model_path / 'input_params.json', 'r') as f:
    input_params = json.load(f)
ngram_range = input_params['ngram_range']
maxlen = input_params['maxlen']

# Code Lookups
with open('./model/codes_map.json', 'r') as f:
    code_index = json.load(f)
code_lookup = {v: k for k, v in code_index.items()}

# Code description lookup
with open('./model/code_descriptions.json') as f:
    code_descriptions = json.load(f)

# Input Encoders
tokenizer = joblib.load(model_path / 'tokenizer.joblib')
token_index = joblib.load(model_path / 'token_index.joblib')

def load_model():
    global model
    with open(model_path / 'architecture.json', 'r') as f:
        model = model_from_json(json.load(f))
        model.load_weights(model_path / 'weights.h5')
        model.predict(np.zeros(maxlen).reshape(1, -1))
    return model


from keras.preprocessing import sequence

def create_ngram_set(input_list, ngram_value=2):
    """
    Extract a set of n-grams from a list of integers.
    >>> create_ngram_set([1, 4, 9, 4, 1, 4], ngram_value=2)
    {(4, 9), (4, 1), (1, 4), (9, 4)}
    >>> create_ngram_set([1, 4, 9, 4, 1, 4], ngram_value=3)
    [(1, 4, 9), (4, 9, 4), (9, 4, 1), (4, 1, 4)]
    """
    return set(zip(*[input_list[i:] for i in range(ngram_value)]))


def add_ngram(sequences, token_indice, ngram_range=2):
    """
    Augment the input list of list (sequences) by appending n-grams values.
    Example: adding bi-gram
    >>> sequences = [[1, 3, 4, 5], [1, 3, 7, 9, 2]]
    >>> token_indice = {(1, 3): 1337, (9, 2): 42, (4, 5): 2017}
    >>> add_ngram(sequences, token_indice, ngram_range=2)
    [[1, 3, 4, 5, 1337, 2017], [1, 3, 7, 9, 2, 1337, 42]]
    Example: adding tri-gram
    >>> sequences = [[1, 3, 4, 5], [1, 3, 7, 9, 2]]
    >>> token_indice = {(1, 3): 1337, (9, 2): 42, (4, 5): 2017, (7, 9, 2): 2018}
    >>> add_ngram(sequences, token_indice, ngram_range=3)
    [[1, 3, 4, 5, 1337], [1, 3, 7, 9, 2, 1337, 2018]]
    """
    new_sequences = []
    for input_list in sequences:
        new_list = input_list[:]
        for i in range(len(new_list) - ngram_range + 1):
            for ngram_value in range(2, ngram_range + 1):
                ngram = tuple(new_list[i:i + ngram_value])
                if ngram in token_indice:
                    new_list.append(token_indice[ngram])
        new_sequences.append(new_list)

    return new_sequences

class TextProcessor(object):
    def __init__(self, tokenizer, token_indice, ngram_range, maxlen):
        self.tokenizer = tokenizer
        self.token_indice = token_indice
        self.ngram_range = ngram_range
        self.maxlen = maxlen

    def process(self, texts):
        x = self.tokenizer.texts_to_sequences(texts)
        if self.ngram_range > 1:
            x = add_ngram(x, self.token_indice, self.ngram_range)
        x = sequence.pad_sequences(x, maxlen=self.maxlen)

        return x

text_processor = TextProcessor(tokenizer, token_index, ngram_range=ngram_range, maxlen=maxlen)

def x_input(text):
    return str(text).lower()

def top_n_probabilities(probs_arr,top_n=10):
    top_idx = np.argsort(probs_arr)[-top_n:] # ascending
    return list(reversed(top_idx))

response_description = {
    'description' : 'This description',
    'submitted_data' : {
        'structure' : {
            'drug_text' : 'Text description of drug',
            'prediction_count' : 'Optional. The number of predictions to return (default=10)'
        }
    },
    'info' : {
        'structure' : {
            'warning' : 'A warning if the maximum prediction is under 0.4, demonstrating model uncertainty',
            'time_elapsed' : 'time it took to calculate prediction and build response'
        }
    },
    'predictions' : {
        'description' : 'Array of predicted codes in descending order of probability, each with structure below',
        'structure' : {
            'sc_code': 'predicted SC drug code',
            'code_id': 'ID of code for lookup. Can be ignored. For internal documentation',
            'code_definition': 'Definition of SC Code from documentation',
            'p': 'predicted probability of code given course number and course title',
            'p_rank' : 'Rank of prediction (1 is most likely)'
        }
    }
}

def wiki_lookup(drug_name):
    sparql = SPARQLWrapper("https://query.wikidata.org/bigdata/namespace/wdq/sparql",
                           agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36")  # Needed to avoid getting a 403
    sparql.setQuery(f"""
        SELECT distinct ?moleculeName ?molecule ?exactMatch ?article
        (GROUP_CONCAT(DISTINCT(?altLabel); separator = ", ") AS ?altLabel_list)
        WHERE {{
            VALUES
                ?types {{ wd:Q12140 wd:Q11173 }}
                ?molecule  wdt:P31 ?types
                ; rdfs:label ?moleculeName filter (lang(?moleculeName) = "en") .
            OPTIONAL {{
                ?molecule skos:altLabel ?altLabel .
                FILTER (lang(?altLabel) = "en") .
            }}
            BIND(IF(regex(?moleculeName, "^{drug_name}$") , 0,1) AS ?exactMatch) .
            FILTER ( CONTAINS(LCASE(?moleculeName), "{drug_name}") || CONTAINS(?altLabel, "{drug_name}")) .

            #get the URL
            OPTIONAL {{
                ?article schema:about ?molecule .
                ?article schema:isPartOf <https://en.wikipedia.org/>.
            }}
        }}
        GROUP BY ?moleculeName ?molecule ?exactMatch ?article
        ORDER BY ?exactMatch
        LIMIT 1
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    if len(results['results']['bindings']):
        if 'article' in results['results']['bindings'][0]:
            url = results['results']['bindings'][0]['article']['value']
            return url.split('/')[-1]

    return ''
