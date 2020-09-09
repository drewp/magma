FROM ubuntu:focal

ENV TZ=America/Los_Angeles
ENV LANG=en_US.UTF-8

WORKDIR /opt

RUN apt update
RUN apt install -y tzdata
RUN apt install -y nodejs curl vim-tiny npm python3-pip
RUN npm install -g pnpm

RUN apt install -y git

COPY requirements.txt ./
RUN pip3 install --index-url https://projects.bigasterisk.com/ --extra-index-url https://pypi.org/simple -r requirements.txt
# not sure why this doesn't work from inside requirements.txt
RUN pip3 install --index-url https://projects.bigasterisk.com/ --extra-index-url https://pypi.org/simple -U 'https://github.com/drewp/cyclone/archive/python3.zip?v2'


COPY package.json ./
RUN pnpm install


COPY *.py req* *.n3 *.js *.html *.styl *.json *.jpg *.png ./
RUN mkdir build
#RUN node_modules/jastyco/bin/jastyco -b
RUN cp *.png *.jpg *.js build/
RUN pnpx stylus < style.styl > build/style.css
EXPOSE 8010

CMD [ "python3", "serve_magma.py" ]
