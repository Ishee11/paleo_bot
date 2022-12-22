FROM python:3.10
RUN apt-get update -qu
ADD config.py .
ADD credentials.json .
ADD data.pickle .
ADD paleo_bot.py .
ADD quickstart.py .
ADD start.py .
ADD token.json .
ADD token.pickle .
ADD requirements.txt .
RUN pip install -r requirements.txt
CMD python3 ./paleo_bot.py