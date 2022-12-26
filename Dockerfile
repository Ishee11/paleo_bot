FROM python:3.10
RUN apt-get update -qu

#ENV PYTHONDONTWRITEBYTECODE 1
#ENV PYTHONUNBUFFERED 1
#
#RUN apt-get update && \
#    apt-get install -y --no-install-recommends gcc
#
#RUN python -m venv /opt/venv
#ENV PATH="/opt/venv/bin:$PATH"
#ADD fullchain.pem .
ADD credentials.json .
ADD data.pickle .
ADD quickstart.py .
ADD start.py .
ADD token.json .
ADD token.pickle .
ADD requirements.txt .
ADD config.py .
ADD paleo_bot.py .
RUN pip install -r requirements.txt
WORKDIR .
#ENTRYPOINT ['paleo_bot.py']
CMD python3 ./paleo_bot.py