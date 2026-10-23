# Sandbox-only shim, NOT part of the FreeSWITCH image design.
# This build machine reaches the internet only through an HTTPS proxy, and
# plain-HTTP apt mirrors are not allowed. So the repo's docker/Dockerfile is
# built unmodified on top of this image, tagged locally as
# debian:bookworm-slim. The only differences from the real
# debian:bookworm-slim: apt uses https:// mirrors and a CA bundle (public
# roots + the proxy CA), and the proxy CA is in
# /usr/local/share/ca-certificates (picked up when the repo's Dockerfile
# installs ca-certificates, so git/pip trust it too). On the real box, skip
# this file entirely.
#   build: cp /root/.ccr/agent-proxy-ca.crt proxy-ca.crt; cp /root/.ccr/ca-bundle.crt ca-bundle.crt
#          docker build --network host -t debian:bookworm-slim .
FROM mirror.gcr.io/library/debian:bookworm-slim
COPY proxy-ca.crt /usr/local/share/ca-certificates/sandbox-proxy-ca.crt
COPY ca-bundle.crt /etc/ssl/sandbox-ca-bundle.crt
RUN sed -i 's#http://deb.debian.org#https://deb.debian.org#g' /etc/apt/sources.list.d/debian.sources \
 && printf 'Acquire::https::CAInfo "/etc/ssl/sandbox-ca-bundle.crt";\n' > /etc/apt/apt.conf.d/99sandbox-ca
