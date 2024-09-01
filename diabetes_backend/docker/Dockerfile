FROM python:3.12.4 AS base

RUN mkdir -p /src
RUN mkdir -p /logs
COPY . /src
WORKDIR /src
RUN pip install -r requirements.txt

FROM base AS backend
# TODO: Do this properly
EXPOSE 5000
ENV FLASK_APP=app.py
CMD ["python", "-m", "flask", "run", "--host", "0.0.0.0"]

FROM base AS backend_unit
WORKDIR /src
RUN pip install -r requirements-dev.txt
CMD ["coverage", "run", "-m", "unittest", "discover", "-s", "/src/unit_tests/", "-p", "'*_test.py'", "&&", "coverage", "run", "-m"]
