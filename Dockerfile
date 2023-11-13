FROM astra-new:base

RUN apt-get update && apt-get install -y apt-rdepends dpkg-dev debsecan python3-pip
RUN pip install tabulate

WORKDIR /app

COPY main.py /app/main.py

ENTRYPOINT ["python", "main.py"]