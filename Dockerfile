FROM python:bullseye@sha256:62926a9b37d0d6cd9c9d874c6c0c38d56fe1efa6a1d2cd322f3440907fbfc06b

RUN apt-get update && apt-get install -y apt-rdepends dpkg-dev debsecan
RUN pip install tabulate

WORKDIR /app

COPY main.py /app/main.py

ENTRYPOINT ["python", "main.py"]