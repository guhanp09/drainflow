FROM debian:bookworm-slim@sha256:734a72b3d6142a71993b4bc580ca01d8ca687f77a2c422d96a961d3376b179bc
ENV DEBIAN_FRONTEND=noninteractive QT_QPA_PLATFORM=offscreen
RUN apt-get update && apt-get install -y --no-install-recommends freecad-python3 python3 python3-numpy && rm -rf /var/lib/apt/lists/*
ENV PYTHONPATH=/usr/lib/freecad-python3/lib:/work/src
WORKDIR /work
ENTRYPOINT ["python3"]
