FROM python:3.7-slim

ENV APP_HOME /app
WORKDIR $APP_HOME
COPY proxy.py .

CMD ["/usr/bin/env", "python", "proxy.py"]

