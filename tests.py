import unittest
import json

from app import app

dummy_data = {'drug_section': 'SD15', 'drug_text': 'heroin'}

class TestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def test_submitted_data(self):
        response = self.app.post('/drug-predict/', data=dummy_data)
        data = json.loads(response.get_data(as_text=True))
        submitted_data = data['submitted_data']
        assert 'drug_text' in submitted_data
        assert 'drug_section' in submitted_data

    def test_submitted_data_json(self):
        response = self.app.post('/drug-predict/', data=json.dumps(dummy_data), content_type='application/json')
        data = json.loads(response.get_data(as_text=True))
        submitted_data = data['submitted_data']
        assert 'drug_text' in submitted_data
        assert 'drug_section' in submitted_data

    def test_description(self):
        response = self.app.post('/drug-predict/', data=dummy_data)
        data = json.loads(response.get_data(as_text=True))
        assert 'description' in data

    def test_description(self):
        response = self.app.post('/drug-predict/', data=dummy_data)
        data = json.loads(response.get_data(as_text=True))
        assert 'info' in data
        info_data = data['info']
        assert 'warning' in info_data
        assert 'time_elapsed' in info_data

    def test_prediction_structure(self):
        response = self.app.post('/drug-predict/', data=dummy_data)
        data = json.loads(response.get_data(as_text=True))
        predictions = data['predictions']
        for pred in predictions:
            assert 'sc_code' in pred
            assert 'code_id' in pred
            assert 'code_definition' in pred
            assert 'p' in pred
            assert 'p_rank' in pred

    def test_prediction_values(self):
        response = self.app.post('/drug-predict/', data=dummy_data)
        data = json.loads(response.get_data(as_text=True))
        predictions = data['predictions']
        max_pred = max(pred['p'] for pred in predictions)
        assert max_pred == predictions[0]['p']
    
    def test_bad_request(self):
        response = self.app.post('/drug-predict/', data={})
        data = json.loads(response.get_data(as_text=True))
        assert data == {'error' : 'Data missing drug_section or drug_text variables'}

    def test_warning(self):
        fake_course = {
            'drug_section':'LS01',
            'drug_text':'relaxation brownies'
            }
        response = self.app.post('/drug-predict/', data=fake_course)
        data = json.loads(response.get_data(as_text=True))
        warning = data['info']['warning']
        assert warning == "Max prediction less than 0.4, model is uncertain about this course prediction"

if __name__ == '__main__':
    unittest.main()