FROM nginx:1.27-alpine AS final

ENV PORT=8080

RUN printf 'server {\n\
    listen 8080;\n\
    server_name _;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
    location /healthz {\n\
        access_log off;\n\
        return 200 "{\"status\":\"ok\"}";\n\
        add_header Content-Type application/json;\n\
    }\n\
    location / {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf

COPY css /usr/share/nginx/html/css
COPY data /usr/share/nginx/html/data
COPY images /usr/share/nginx/html/images
COPY js /usr/share/nginx/html/js
COPY index.html /usr/share/nginx/html/index.html

RUN sed -i 's@^pid .*@pid /tmp/nginx.pid;@' /etc/nginx/nginx.conf \
 && sed -i '/^user /d' /etc/nginx/nginx.conf \
 && mkdir -p /tmp/nginx-cache /var/cache/nginx /var/run \
 && chown -R nginx:nginx /tmp/nginx-cache /usr/share/nginx/html /var/cache/nginx /var/run

USER nginx

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget -qO- http://localhost:8080/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]
