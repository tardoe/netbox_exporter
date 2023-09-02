FROM python:3.9
COPY . .
RUN pip install -r requirements.txt
EXPOSE 9000
CMD [ "python", "./netbox_exporter.py" ]