# syntax=docker/dockerfile:1
FROM node:20-alpine AS builder

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
RUN npm run build || true

FROM node:20-alpine

RUN addgroup --gid 1000 nodeuser && adduser --uid 1000 --gid 1000 --home /app --disabled-password nodeuser
COPY --from=builder /app /app

USER nodeuser

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget -qO- http://localhost:3000/healthz || exit 1

CMD ["node", "server.js"]
