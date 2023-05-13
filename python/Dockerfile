FROM alpine

WORKDIR /app

COPY db/items.sql db/items.sql
COPY python python

RUN addgroup -S mercari && adduser -S trainee -G mercari
RUN chown -R trainee:mercari /app/db
RUN chown -R trainee:mercari /app/python/images

RUN apk --update-cache add \
    python3 \
    python3-dev \
    py3-pip \
		sqlite
RUN cat /app/db/items.sql | sqlite3 /app/db/mercari.sqlite3

RUN chown trainee:mercari /app/db/mercari.sqlite3

RUN pip install --upgrade pip
RUN pip install -r /app/python/requirements.txt

USER trainee

WORKDIR /app/python

CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0",  "--port", "9000"]
