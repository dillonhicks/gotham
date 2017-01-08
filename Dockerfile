FROM dillonhicks/gotham:base

ADD . /app
WORKDIR /app

RUN pip install Cython && \
    pip install -r requirements.txt

ENV PATH=/usr/local/go/bin:$PATH
CMD ./bin/build
