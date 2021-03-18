FROM kenhv/kensurbot:debian

RUN set -ex \
    && git clone -b sql-extended https://github.com/SreekanthPalakurthi/PaperplaneExtended.git /root/userbot \
    && chmod 777 /root/userbot

WORKDIR /root/userbot/

CMD ["python3", "-m", "userbot"]
