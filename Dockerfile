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

# The IDC-patched GrandQC fork is fetched at build time (not vendored).
RUN git clone --depth 1 --branch idc-dicom-wsidicom \
        https://github.com/fedorov/grandqc.git external/grandqc

# Sanity check: the data-free tests must pass in the image.
RUN pytest tests/ -q

CMD ["bash"]
