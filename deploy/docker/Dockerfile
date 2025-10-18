FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY ./src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src/ .

RUN mkdir -p data

RUN echo '#!/bin/bash\n\
if [ "$1" = "api" ]; then\n\
    exec uvicorn api_server:app --host 0.0.0.0 --port 8000\n\
elif [ "$1" = "etl" ]; then\n\
    exec python check_and_update.py\n\
else\n\
    echo "Usage: docker run <image> [api|etl]"\n\
    exit 1\n\
fi' > /app/start.sh && chmod +x /app/start.sh

EXPOSE 8000

CMD ["/app/start.sh"]