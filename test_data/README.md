# Diabetes database

A docker based database container.

Running the service, that starts a postgres instance with user diabetes, and database diabetes.
The table by default is the `glucose_times`
```sh
./build.sh
./run.sh
docker exec -it diabetes-db psql -U diabetes
./stop.sh
```

## Export data

### Glucose
```sh
docker exec -it app-db \
    psql -U diabetes_root -d diabetes_data \
    -c "COPY (SELECT * FROM glucose_times ORDER BY id) TO STDOUT WITH (FORMAT CSV, HEADER)" > glucose.csv
```

### Import
```sh
docker exec -it app-db     psql -U diabetes_root -d diabetes_data     -c "COPY glucose_times FROM '/test_data/glucose.csv' CSV HEADER;"
```

### Strava

### Export
```sh
docker exec -it app-db \
    psql -U diabetes_root -d diabetes_data \
    -c "COPY (SELECT * FROM activities ORDER BY id) TO STDOUT WITH (FORMAT CSV, HEADER)" > activities.csv
```

### Import
```sh
docker exec -it app-db     psql -U diabetes_root -d diabetes_data     -c "COPY activities FROM '/path/to/csv/ZIP_CODES.txt' WITH (FORMAT csv);
```


## Dump DB
```sh
docker exec -it app-db \
pg_dump -U diabetes_root -d diabetes_data >> sqlfile.sql
```
