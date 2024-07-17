FROM python:3.12.4 as base

RUN mkdir -p src
COPY . /src
WORKDIR /src
RUN pip install -r requirements.txt

FROM base as backend
CMD ["python", "glucose.py" ]

FROM base as backend_unit
CMD python -m unittest discover -s ./unit_tests/ -p '*_test.py'