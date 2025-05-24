# Example Dockerfile at templates/static/Dockerfile
FROM nginx:alpine # Or some other lightweight web server

COPY static/ /usr/share/nginx/html/ 
# Assuming nginx serves from /usr/share/nginx/html

# If the Dockerfile is specifically meant to copy *only* the content within templates/static
# COPY . /usr/share/nginx/html/ # This also works if the Dockerfile is inside static/ and context is templates/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]