FROM python:3.12-slim

WORKDIR /app

# System deps for pymupdf and python-docx
RUN apt-get update && apt-get install -y \
    libmupdf-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry — set POETRY_HOME explicitly so the PATH
# is predictable across all Docker build environments
ENV POETRY_HOME="/opt/poetry"
ENV PATH="${POETRY_HOME}/bin:${PATH}"

RUN curl -sSL https://install.python-poetry.org | python3 -

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-root --only main --no-interaction --no-ansi

COPY api/ .

EXPOSE 8082

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8082", "--reload"]