FROM nginx:alpine

# Limpa os arquivos padrão do Nginx para não dar conflito
RUN rm -rf /usr/share/nginx/html/*

# Copia os arquivos do frontend para a pasta correta
COPY frontend/ /usr/share/nginx/html/

# Copia a nossa configuração customizada
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
