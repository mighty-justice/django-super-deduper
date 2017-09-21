FROM python:3.6-alpine3.6

ENV APP_DIR /app

RUN addgroup -S mighty && adduser -S -G mighty mighty

RUN apk add --no-cache gcc musl-dev

WORKDIR $APP_DIR

COPY requirements-test.txt $APP_DIR
RUN pip install --no-cache-dir -r requirements-test.txt \
    && find / -type d -name '__pycache__' -print0 | xargs -r0 -- rm -r


COPY requirements.txt $APP_DIR
RUN pip install --no-cache-dir -r requirements.txt \
    && find / -type d -name '__pycache__' -print0 | xargs -r0 -- rm -r

COPY . $APP_DIR
