FROM locustio/locust:latest

WORKDIR /mnt/locust

COPY locustfile.py .

EXPOSE 8089

ENTRYPOINT ["locust", "-f", "/mnt/locust/locustfile.py"]
