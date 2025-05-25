# db.Dockerfile
FROM postgres:15
# Base off the official image

# Copy your init script into the entrypoint directory
COPY docker-entrypoint-initdb.d/01-create-menu-table.sql /docker-entrypoint-initdb.d/

# The original entrypoint is inherited, it will find and run this script