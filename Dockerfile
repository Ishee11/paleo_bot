FROM python:3.10
RUN apt-get update -qu

ADD credentials.json .
ADD data.pickle .
ADD button.png .
ADD quickstart.py .
ADD start.py .
ADD token.json .
ADD token.pickle .
ADD requirements.txt .
ADD config.py .
ADD paleo_bot.py .
RUN pip install -r requirements.txt
WORKDIR .

CMD python3 ./paleo_bot.py