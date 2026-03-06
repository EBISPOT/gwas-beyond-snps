# ── Stage 1: build ────────────────────────────────────────────────────────────
# Needs both Node.js (Docusaurus) and Python/uv (prebuild step builds the
# sumstatlib wheel and stages the web validator into static/).
FROM node:22-slim AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 curl ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv (required by the prebuild script)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Copy workspace configuration and Python source required by uv build
COPY pyproject.toml ./
COPY README.md ./
COPY sumstatlib/ ./sumstatlib/
COPY src/ ./src/

# Copy the Docusaurus site
COPY docs/ ./docs/

# Install Node dependencies
WORKDIR /app/docs
RUN npm ci

# prebuild: builds the sumstatlib wheel and stages the web validator
# build:    runs Docusaurus; output lands in /app/docs/build/
RUN npm run build

# ── Stage 2: serve ────────────────────────────────────────────────────────────
FROM nginx:alpine AS server

# Place the built site under the production base path so asset URLs resolve
COPY --from=builder /app/docs/build /usr/share/nginx/html/gwas/apps/beyond-snps

COPY deployment/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
