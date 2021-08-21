FROM ubuntu:20.10

ENV TZ=America/Los_Angeles
ENV LANG=en_US.UTF-8

WORKDIR /opt

RUN apt update
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata

RUN apt install -y wget git xz-utils less curl vim-tiny npm python3-pip

RUN wget --output-document=node.tar.xz https://nodejs.org/dist/v14.16.0/node-v14.16.0-linux-x64.tar.xz && \
    tar xf node.tar.xz && \
    ln -s node*x64 nodejs

ENV PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/opt/nodejs/bin
RUN node /opt/nodejs/bin/npm install -g pnpm

COPY requirements.txt ./
RUN pip3 install --index-url https://projects.bigasterisk.com/ --extra-index-url https://pypi.org/simple -r requirements.txt

COPY package.json ./
RUN pnpm install

COPY *.py req* *.n3 *.js *.html *.styl *.json *.jpg *.png ./
RUN mkdir build
#RUN node_modules/jastyco/bin/jastyco -b
RUN cp *.png *.jpg *.js build/
RUN pnpx stylus < style.styl > build/style.css
EXPOSE 8010

CMD [ "python3", "serve_magma.py" ]
