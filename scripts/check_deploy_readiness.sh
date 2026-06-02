#!/usr/bin/env bash
set -euo pipefail

ENVIRONMENT="${1:-staging}"

REQUIRED_SECRETS=(
  SSH_PRIVATE_KEY
  SSH_KNOWN_HOSTS
  SSH_USER
  SSH_HOST
  DJANGO_SECRET_KEY
  DJANGO_ALLOWED_HOSTS
  CORS_ALLOWED_ORIGINS
  CSRF_TRUSTED_ORIGINS
  JWT_SECRET_KEY
  MONGODB_URI
  FIREBASE_CREDENTIALS_JSON
  GOOGLE_APPLICATION_CREDENTIALS_JSON
  ANTHROPIC_API_KEY
  OPENAI_API_KEY
  TERAMINA_LLM_API
  TERAMINA_API_KEY
  SUMMARY_MODEL
  PINECONE_API_KEY
  PINECONE_INDEX
  GS_BUCKET_NAME
  GS_PROJECT_ID
  GS_VDB_BUCKET_NAME
  CELERY_BROKER_URL
  CELERY_RESULT_BACKEND
  CACHE_REDIS_URL
  SENTRY_DSN
  DATA_UPLOAD_MAX_MB
  FILE_UPLOAD_MAX_MB
  VITE_ENDPOINT
  VITE_FIREBASE_PROJECT_ID
  VITE_FIREBASE_API_KEY
  VITE_FIREBASE_STORAGE_BUCKET
  VITE_FIREBASE_AUTH_DOMAIN
  VITE_FIREBASE_MESSAGING_SENDER_ID
  VITE_FIREBASE_APP_ID
  VITE_FIREBASE_MEASUREMENT_ID
  VITE_FIREBASE_VAPID_KEY
  VITE_SUMMARY_MODEL
  VITE_SENTRY_DSN
  VITE_GA_MEASUREMENT_ID
)

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI is required."
  exit 1
fi

echo "Checking GitHub Actions deployment readiness for environment: ${ENVIRONMENT}"
echo

echo "Workflows:"
gh workflow list
echo

echo "Environment:"
if ! gh api "repos/:owner/:repo/environments/${ENVIRONMENT}" --jq '.name' >/dev/null; then
  echo "Missing GitHub environment: ${ENVIRONMENT}"
  exit 1
fi
echo "- ${ENVIRONMENT} exists"
echo

SECRET_NAMES="$(gh secret list --env "${ENVIRONMENT}" --json name --jq '.[].name')"

missing=()
for secret in "${REQUIRED_SECRETS[@]}"; do
  if ! grep -qx "${secret}" <<< "${SECRET_NAMES}"; then
    missing+=("${secret}")
  fi
done

if [ "${#missing[@]}" -gt 0 ]; then
  echo "Missing ${#missing[@]} required secret(s):"
  printf -- "- %s\n" "${missing[@]}"
  exit 1
fi

echo "All required secrets are present for ${ENVIRONMENT}."
