FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN addgroup --system aromatwin && adduser --system --ingroup aromatwin aromatwin
WORKDIR /app

COPY pyproject.toml README.md LICENSE.md ./
COPY src ./src
COPY static ./static
COPY data/*.csv ./data/
RUN python -m pip install --upgrade pip && python -m pip install .

USER aromatwin
EXPOSE 8000
CMD ["uvicorn", "aromatwin.main:app", "--host", "0.0.0.0", "--port", "8000"]
