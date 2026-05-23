FROM python:3.12-alpine

WORKDIR /app

COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./templates ./templates
COPY ./dnsmasq_leases_ui.py ./

EXPOSE 5000
CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "2", "dnsmasq_leases_ui:app"]
