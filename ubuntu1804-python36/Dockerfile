# ベースとなるイメージ
FROM ubuntu:18.04

# RUNでコンテナ生成時に実行する
RUN apt-get update
RUN apt-get install -y python3.8
RUN ln -s /usr/bin/python3.8 /usr/bin/python
RUN ln -s /usr/bin/python3.8 /usr/bin/python3
RUN apt-get install -y python3-pip
RUN pip3 install beautifulsoup4
RUN pip3 install urllib3
RUN pip3 install lxml
RUN apt-get install -y git

RUN export LC_CTYPE="C.UTF-8"
