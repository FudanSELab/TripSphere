# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json bun.lock ./

# Install dependencies using npm (since bun.lock is present, we'll use npm for Docker)
RUN npm install --frozen-lockfile

# Copy generated proto files and source code
COPY lib ./lib
COPY app ./app
COPY components ./components
COPY public ./public
COPY next.config.ts tsconfig.json ./
COPY postcss.config.mjs eslint.config.mjs ./

# Build the application
RUN npm run build


# Production stage
FROM node:20-alpine AS runner

WORKDIR /app

# Setup a non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy necessary files from builder
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Change ownership
RUN chown -R nextjs:nodejs /app

# Use the non-root user
USER nextjs

EXPOSE 3000

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]

