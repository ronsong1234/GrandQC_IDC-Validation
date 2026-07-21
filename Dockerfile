# Reproducible environment for the CLI workflow and tests.
# GPU is optional (GrandQC auto-selects CUDA when present); this image is CPU by default.
FROM python:3.11-slim

# libopenslide is needed only for the .svs baseline arm; wsidicom handles DICOM.
RUN apt-get update && apt-get install -y --no-install-recommends \
        openslide-tools libgl1 git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements-lock.txt .
RUN pip install --no-cache-dir -r requirements-lock.txt

COPY . .

# Install the package itself (deps already pinned above; --no-deps keeps the lock).
RUN pip install --no-cache-dir --no-deps -e .

# The IDC-patched GrandQC fork is fetched at build time (not vendored), pinned to the
# validated commit rather than the moving branch head.
RUN git clone https://github.com/fedorov/grandqc.git external/grandqc \
    && git -C external/grandqc checkout 1d9807be7b3a04de2f0cc5d799b55d9fd961f01e

# Sanity check: the data-free tests must pass in the image.
RUN pytest tests/ -q

CMD ["bash"]
