# =========================================================
# Frontend Dockerfile — Multi-stage Build
# =========================================================

FROM node:20-alpine AS base

WORKDIR /app

# --- Development Stage ---
FROM base AS development

COPY package*.json ./
RUN npm install --legacy-peer-deps

COPY . .

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["npm", "run", "dev"]

# --- Production Stage ---
FROM base AS production

ENV NODE_ENV=production

COPY package*.json ./
RUN npm install --legacy-peer-deps

COPY . .
RUN npm run build

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["npm", "run", "start"]
