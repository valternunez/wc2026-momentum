# Railway daily-scrape image. The repo is cloned onto a volume at runtime (see daily.sh),
# so the image only needs git + uv + the entrypoint. Run on a cron schedule (e.g. 30 13 * * *).
FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv

COPY daily.sh /daily.sh
RUN chmod +x /daily.sh

CMD ["/daily.sh"]
