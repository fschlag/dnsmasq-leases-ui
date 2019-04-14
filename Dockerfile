FROM python:3.6.8-alpine

RUN echo '* Installing OS dependencies' \
  && apk add --update --no-cache build-base

WORKDIR /app
COPY ./requirements.txt ./

RUN echo '* Installing Python dependencies' \
  && pip install -r requirements.txt \
  && echo '* Removing unneeded OS packages' \
  && apk del build-base


COPY ./templates ./templates
COPY ./dnsmasq-leases-ui.py ./

EXPOSE 5000
CMD ["python", "dnsmasq-leases-ui.py"]
