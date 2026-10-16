# deploy/tls — сертификаты (вне git)

Файлы cert.pem / key.pem исключены из репо (.gitignore: deploy/tls/*.pem)
— это секреты. Источник истины: /etc/ssl/certs/autoschool-cert.pem и
/etc/ssl/private/autoschool-key.pem на сервере.

~/service-start.sh подставляет эти пути в nginx-конфиг через sed и при
их отсутствии завершается с инструкцией (INC-006, см. incidents.md).
