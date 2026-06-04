# Build stage
FROM node:20 AS build

ARG VITE_ENDPOINT
ARG VITE_FIREBASE_PROJECT_ID
ARG VITE_FIREBASE_API_KEY
ARG VITE_FIREBASE_STORAGE_BUCKET
ARG VITE_FIREBASE_AUTH_DOMAIN
ARG VITE_FIREBASE_MESSAGING_SENDER_ID
ARG VITE_FIREBASE_APP_ID
ARG VITE_FIREBASE_MEASUREMENT_ID
ARG VITE_FIREBASE_VAPID_KEY
ARG VITE_SUMMARY_MODEL
ARG VITE_SENTRY_DSN
ARG VITE_GA_MEASUREMENT_ID

RUN /bin/sh -c 'if [ -z "$VITE_ENDPOINT" ]; then echo "Error: VITE_ENDPOINT is empty"; exit 1; fi'
RUN /bin/sh -c 'if [ -z "$VITE_FIREBASE_PROJECT_ID" ]; then echo "Error: VITE_FIREBASE_PROJECT_ID is empty"; exit 1; fi'

WORKDIR /app
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile
COPY . .

RUN yarn build

# Production stage — nginx-unprivileged runs as uid 101, never root
FROM nginxinc/nginx-unprivileged:alpine
WORKDIR /usr/share/nginx/html

COPY --from=build /app/dist .
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
