# templates/Dockerfile
FROM nginx:alpine

# Copy everything into web root
COPY . /usr/share/nginx/html/

# Replace Nginx's default.conf if you need custom routing (optional)
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# Add entrypoint script to inject env.js
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
