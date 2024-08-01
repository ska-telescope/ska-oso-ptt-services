ARG BUILD_IMAGE="artefact.skao.int/ska-tango-images-pytango-builder:9.5.0"
ARG BASE_IMAGE="artefact.skao.int/ska-tango-images-pytango-runtime:9.5.0"

FROM $BUILD_IMAGE AS buildenv
FROM $BASE_IMAGE AS runtime

ARG CAR_PYPI_REPOSITORY_URL=https://artefact.skao.int/repository/pypi-internal
ENV PIP_INDEX_URL=${CAR_PYPI_REPOSITORY_URL}

USER root

WORKDIR /app

# Copy poetry.lock* in case it doesn't exist in the repo
COPY pyproject.toml poetry.lock* ./
COPY ska_db_oda-5.3.0-py3-none-any.whl /app
COPY ska_oso_pdm-15.1.0-py3-none-any.whl /app

# Install runtime dependencies and the app
RUN poetry config virtualenvs.create false
# Developers may want to add --dev to the poetry export for testing inside a container
RUN poetry export --format requirements.txt --output poetry-requirements.txt --without-hashes && \
    pip install -r poetry-requirements.txt && \
    pip install . && \
    rm poetry-requirements.txt

RUN pip install ska_oso_pdm-15.2.0-py3-none-any.whl --force
RUN pip install ska_db_oda-5.3.0-py3-none-any.whl --force

USER tango

CMD ["python3", "-m", "ska_oso_ptt_services.rest.wsgi"]
