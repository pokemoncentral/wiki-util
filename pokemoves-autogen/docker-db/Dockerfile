FROM postgres:9.6-alpine
COPY create-tables.sql /docker-entrypoint-initdb.d/
COPY load-pokes.sh /docker-entrypoint-initdb.d/
COPY sourcecsv/*.csv /data/sourcecsv/
