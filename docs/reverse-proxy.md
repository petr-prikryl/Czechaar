# Reverse Proxy

Czecharr intentionally has no built-in authentication. Expose it only through a trusted network boundary, VPN, reverse proxy authentication, or an IP allowlist.

## Nginx

```nginx
server {
    listen 443 ssl http2;
    server_name czecharr.example.com;

    client_max_body_size 1m;

    # Optional allowlist.
    # allow 192.0.2.0/24;
    # deny all;

    location / {
        proxy_pass http://127.0.0.1:8787;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }
}
```

WebSockets are not required by the first release; scan progress uses polling.

## Traefik

```yaml
services:
  czecharr:
    labels:
      - traefik.enable=true
      - traefik.http.routers.czecharr.rule=Host(`czecharr.example.com`)
      - traefik.http.routers.czecharr.entrypoints=websecure
      - traefik.http.routers.czecharr.tls.certresolver=letsencrypt
      - traefik.http.services.czecharr.loadbalancer.server.port=8080
      - traefik.http.middlewares.czecharr-allowlist.ipallowlist.sourcerange=192.0.2.0/24
      - traefik.http.routers.czecharr.middlewares=czecharr-allowlist
```

Use HTTPS for any browser access outside a fully trusted local network.
