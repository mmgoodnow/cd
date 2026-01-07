FROM alpine:3.20

# Minimal image so CI workflows that require a Dockerfile can run.
CMD ["/bin/sh"]
