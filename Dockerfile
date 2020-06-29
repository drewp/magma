FROM bang5:5000/base_x86

WORKDIR /opt

COPY requirements.txt ./
RUN pip3 install --index-url https://projects.bigasterisk.com/ --extra-index-url https://pypi.org/simple -r requirements.txt
# not sure why this doesn't work from inside requirements.txt
RUN pip3 install --index-url https://projects.bigasterisk.com/ --extra-index-url https://pypi.org/simple -U 'https://github.com/drewp/cyclone/archive/python3.zip?v2'



COPY *.py req* *.n3 *.html ./

# still uses makefile
COPY build ./build

EXPOSE 8010

CMD [ "python3", "serve_magma.py" ]
