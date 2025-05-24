#!/bin/sh

# Write dynamic env.js to the frontend root
cat <<EOF > /usr/share/nginx/html/env.js
window.env = {
  REACT_APP_API_URL: "${REACT_APP_API_URL}"
};
EOF

# Start nginx
exec "$@"
