# templates/Dockerfile
FROM nginx:alpine

# Remove the default Nginx config file
RUN rm /etc/nginx/conf.d/default.conf

# Copy your custom Nginx config into the conf.d directory
COPY nginx-proxy.conf /etc/nginx/conf.d/

# Copy your frontend static assets into the Nginx web root
# Make sure the path '.' is correct for where your static files are relative to the Dockerfile
COPY . /usr/share/nginx/html/

# EXPOSE 80 # Optional, but good practice

# CMD ["nginx", "-g", "daemon off;"] # Default for nginx:alpine, often not needed to specify