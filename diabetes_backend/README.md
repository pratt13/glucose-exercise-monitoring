# README

## Requirements

* Python
* Postgres Database (db table)

## Setup
```sh
python3 -m venv back-venv
source back-venv/bin/activate
pip install -r requirements.txt
```

## Unit Tests

```sh
python -m unittest discover -s ./src/unit_tests/ -p '*_test.py'
```