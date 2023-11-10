FROM astra@sha256:e8d5f3d966f8c7632041fc509705359af09f03d4ee2ef18842386a940f0c7187

RUN apt-get update && apt-get install -y apt-rdepends dpkg-dev debsecan
RUN pip install tabulate

WORKDIR /app

COPY main.py /app/main.py

ENTRYPOINT ["python", "main.py"]