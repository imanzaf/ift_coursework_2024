FROM postgres:11-alpine

ARG USER_ID=iftbigdata
ENV USER_ID $USER_ID

# refresh os
RUN apk update && apk upgrade

# get sqlite3 alpine
RUN apk add --no-cache sqlite-libs sqlite sqlite-dev
# ubuntu
# RUN apt-get install -y sqlite3 libsqlite3-dev

# make home
RUN mkdir /home/${USER_ID}/ 
COPY ./000.Database/SQL/Equity.db /home/${USER_ID}/

# load postgres
# data dump from sqlite needs to be in this order else will fail on primary/foreign keys
COPY ./000.Database/SQL/create_db.sql /home/${USER_ID}/
COPY ./000.Database/SQL/create_tables.sql /home/${USER_ID}/

# create db, tables and backfill database
CMD psql -d 'postgres://postgres:postgres@postgres_db_cw:5432' -a -f /home/${USER_ID}/create_db.sql \
    && psql -d 'postgres://postgres:postgres@postgres_db_cw:5432/fift' -a -f /home/${USER_ID}/create_tables.sql \
	&& sqlite3 -header -csv /home/${USER_ID}/Equity.db "select * from equity_static;" > /home/company_static.csv \
	&& chmod 777 /home/company_static.csv \
	&& psql -c "TRUNCATE csr_reporting.company_static;" -d 'postgres://postgres:postgres@postgres_db_cw:5432/fift'\
	&& psql -c "\copy csr_reporting.company_static FROM /home/company_static.csv WITH csv HEADER;" -d 'postgres://postgres:postgres@postgres_db_cw:5432/fift'\
	&& rm /home/*.csv 