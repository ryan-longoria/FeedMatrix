# --- Builder Stage ---
FROM node:18-bullseye as builder
WORKDIR /app

# 1. Let Corepack give us Yarn 4
RUN corepack enable && corepack prepare yarn@4.4.1 --activate

# 2. Copy source and install dependencies
COPY . .
RUN yarn install --immutable

# 3. Build the backend
RUN yarn tsc
RUN yarn build:backend

# --- Final Stage ---
FROM node:18-bullseye
WORKDIR /app

# 4. Copy the entire node_modules from builder
COPY --from=builder /app/node_modules ./node_modules

# Also copy any Yarn lockfiles if you want them
COPY --from=builder /app/package.json /app/yarn.lock ./

# 5. Copy the built dist
COPY --from=builder /app/packages/backend/dist packages/backend/dist

COPY app-config*.yaml ./

ENV NODE_ENV=production
ENV PORT=7007
EXPOSE 7007

CMD ["sh", "-c", "tar -xzf packages/backend/dist/bundle.tar.gz && node packages/backend --config app-config.yaml --config app-config.production.yaml"]