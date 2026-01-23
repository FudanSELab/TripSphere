# Build stage
FROM oven/bun:alpine AS builder

WORKDIR /app

# Build arguments for rewrites destinations
ARG HTTP_CHAT_URL=http://trip-chat-service:24210
ARG HTTP_ITINERARY_PLANNER_URL=http://trip-itinerary-planner:24215

# Convert ARGs to ENVs for next build
ENV HTTP_CHAT_URL=$HTTP_CHAT_URL
ENV HTTP_ITINERARY_PLANNER_URL=$HTTP_ITINERARY_PLANNER_URL

# Copy package files
COPY package.json bun.lock ./

# Install dependencies
RUN bun install --frozen-lockfile

# Copy configuration files
COPY next.config.ts tsconfig.json ./
COPY postcss.config.mjs eslint.config.mjs ./

# Copy source code and generated proto files
COPY lib ./lib
COPY app ./app
COPY components ./components
COPY public ./public

# Build the application
RUN bun run build


# Production stage
FROM oven/bun:alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Runtime environment variables for API Routes (SSE proxy)
# These can be overridden by docker-compose environment
ENV HTTP_CHAT_URL=http://trip-chat-service:24210
ENV HTTP_ITINERARY_PLANNER_URL=http://trip-itinerary-planner:24215

# Setup a non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy necessary files from builder
# Note: standalone output includes all necessary dependencies
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Use the non-root user
USER nextjs

EXPOSE 3000

CMD ["bun", "server.js"]
