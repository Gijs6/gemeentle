FROM python:3.10

RUN apt-get update && apt-get install -y locales \
    && sed -i '/nl_NL.UTF-8/s/^# //g' /etc/locale.gen \
    && locale-gen \
    && update-locale LANG=nl_NL.UTF-8
ENV LANG=nl_NL.UTF-8
ENV LANGUAGE=nl_NL:nl
ENV LC_ALL=nl_NL.UTF-8
ENV TZ=Europe/Amsterdam

WORKDIR /app
COPY ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:4000", "app:app"]
