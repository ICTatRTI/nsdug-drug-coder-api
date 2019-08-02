## NSDUH - Drug Coder API

This is a flask app that provides an interface to a predictive model that will predict a NSDUH SC Drug Code given a drug response section and text entry.

## Local Use

The API is available through a docker container. 

1. You'll first have to build the container with `$ docker build -t self/nsduh-drug-coder <repository-folder>`
2. Run the container with `docker run -d -p 8080:8080 self/nsduh-drug-coder`. Change the second port `8080` to whatever port you want to expose the API on.
3. Test with curl:

 ```bash
 curl -d '{"drug_text":"heroin"}' -H "Content-Type: application/json" -X POST http://localhost:8080/drug-predict/
 ```

4. You can also specify the number of predictions to return:
```bash
 curl -d '{"drug_text":"heroin", "prediction_count":25}' -H "Content-Type: application/json" -X POST http://localhost:8080/drug-predict/
 ```

## Response Structure

```json
{
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
```


## OLD Local Use (Python Environment)

Create a virtual environemnt, activate it, and install requirements from pip.

`$ pip install -r requirements.txt`

Then, startup the application with:

`$ flask run` 

Then, test with `curl`:

`$ curl -d '{"drug_section":"SD15", "drug_text":"heroin"}' -H "Content-Type: application/json" -X POST http://localhost:23432/drug-predict/`

Or use something like [Insomnia](https://insomnia.rest/).

## Tests

To run tests use:

`$ python tests.py`

## Misc

Set environment variables by doing the following (assuming your .env contains the right variables):

`$ set -a; source .env`