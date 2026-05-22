# Minimal Caddy container that serves the landing in docs/.
# Used by the Railway deployment for susurro.live.
# The GitHub Pages deploy uses the same docs/ folder — single source of truth.

FROM caddy:2-alpine

COPY Caddyfile /etc/caddy/Caddyfile
COPY docs/ /srv

# Railway provides $PORT; the Caddyfile reads it. EXPOSE is documentation only.
EXPOSE 80
