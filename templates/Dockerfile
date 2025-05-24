# templates/Dockerfile  <-- This file is located at your_project_root/templates/Dockerfile
FROM nginx:alpine

# Remove the default Nginx config file
RUN rm /etc/nginx/conf.d/default.conf

# Copy your custom config file from the build context (templates/)
# Assumes nginx-proxy.conf is in the SAME directory as this Dockerfile
COPY nginx-proxy.conf /etc/nginx/conf.d/

# Copy ONLY the static assets (html files and the static directory)
# Explicitly list the files and the static directory from the build context (templates/)
COPY index.html /usr/share/nginx/html/
COPY menu.html /usr/share/nginx/html/
COPY cart.html /usr/share/nginx/html/
COPY static/ /usr/share/nginx/html/static/ # Copy the static directory recursively

EXPOSE 80

# CMD ["nginx", "-g", "daemon off;"] # Default for nginx:alpine, often not needed to specify