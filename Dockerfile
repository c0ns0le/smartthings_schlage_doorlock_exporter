FROM python:3

RUN mkdir /src
ADD CHANGES.md README.md setup.py requirements.txt ssde.py /src/

RUN pip --no-cache-dir install --upgrade pip setuptools
RUN pip --no-cache-dir install --upgrade -r /src/requirements.txt
RUN pip --no-cache-dir install /src/

CMD ["ssde"]
