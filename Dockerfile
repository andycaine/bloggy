FROM alpine:3.17 as builder

RUN apk add --no-cache python3 curl

WORKDIR /app
RUN mkdir /root/.aws
RUN echo "[default]\nregion=us-west-2" > ~/.aws/config
RUN python3 -m venv .venv
ENV PATH="/app/.venv/bin:$PATH"

COPY . ./bloggy
RUN pip install ./bloggy
RUN pip install Waitress
RUN pip install boto3
RUN pip uninstall -y setuptools
RUN pip uninstall -y pip


FROM alpine:3.17

RUN apk add --no-cache python3 curl

ENV APP_USER=app_user
RUN addgroup $APP_USER
RUN adduser -D -h /app -g -u $APP_USER --system --shell /bin/false --disabled-password

WORKDIR /app
RUN mkdir -p ./.aws
RUN echo -e "[default]\nregion=eu-west-2" > ./.aws/config

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

RUN chown -R ${APP_USER}: /app

USER app_user

HEALTHCHECK --interval=30s --timeout=10s \
  CMD curl -f http://localhost:8080/ping/ || exit 1

EXPOSE 8080
CMD ["waitress-serve", "--call", "bloggy:create_app"]
