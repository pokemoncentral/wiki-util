FROM postgres:9.6-alpine
COPY sourcecsv/*.csv /data/sourcecsv/
COPY create-tables.sql /docker-entrypoint-initdb.d/
COPY load-pokes.sh /docker-entrypoint-initdb.d/
