# Email Ingestion Service

GCP Cloud Function for ingesting emails from email providers (Gmail, IMAP, etc.) and storing them in the database for processing.

## Overview

This service implements Phase 2.1: Email Ingestion from the technical roadmap. It:

- Fetches emails from email providers using the provider-agnostic `EmailService` interface
- Validates senders against the `sender_whitelist` table
- Stores email metadata in the `emails` table
- Downloads attachments and uploads them to Cloud Storage
- Marks emails as processed in the provider
- Logs processing results

## Architecture

### Provider-Agnostic Design

The service uses the `EmailService` interface, enabling support for multiple email providers:

- **Gmail API** (✅ Implemented) - OAuth2 authentication
- **IMAP** (⏳ TODO) - Username/password or OAuth2
- **SendGrid** (⏳ TODO) - API key
- **Mailgun** (⏳ TODO) - API key
- **Microsoft Graph** (⏳ TODO) - OAuth2 for Office 365

### Components

- **`EmailService` Interface** - Provider-agnostic interface
- **`GmailEmailService`** - Gmail API implementation
- **`EmailServiceFactory`** - Factory for creating provider instances
- **`main.py`** - Cloud Function entry point

## Setup

### Prerequisites

- GCP project with Cloud Functions enabled
- Supabase project with database schema deployed
- GCP Cloud Storage bucket for attachments
- Email provider credentials (Gmail OAuth2, etc.)

### Environment Variables

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# GCP
GCP_PROJECT_ID=your-gcp-project-id
STORAGE_BUCKET=email-attachments

# Email Provider
EMAIL_PROVIDER_TYPE=gmail
INBOX_ADDRESS=documents@mybuildingboard.com

# Gmail API (if using Gmail)
GMAIL_CLIENT_ID=your-client-id
GMAIL_CLIENT_SECRET=your-client-secret
GMAIL_REFRESH_TOKEN=your-refresh-token
```

### Deployment

```bash
# Deploy to GCP Cloud Functions
gcloud functions deploy email-ingestion \
  --runtime python311 \
  --trigger-http \
  --memory 512MB \
  --timeout 540s \
  --set-env-vars SUPABASE_URL=...,SUPABASE_SERVICE_ROLE_KEY=...,GCP_PROJECT_ID=...

# Set up Cloud Scheduler trigger (every 5-10 minutes)
gcloud scheduler jobs create http email-ingestion-trigger \
  --schedule="*/5 * * * *" \
  --uri="https://your-region-your-project.cloudfunctions.net/email-ingestion" \
  --http-method=POST
```

## Usage

The Cloud Function is triggered by Cloud Scheduler (every 5-10 minutes) or Pub/Sub.

### Processing Flow

1. **Fetch Emails** - Uses `EmailService.fetchEmails()` to get unprocessed emails
2. **Filter by Sender** - Checks `sender_whitelist` table
3. **Detect App ID** - Determines app_id from sender email (TODO: implement)
4. **Store Email** - Inserts into `emails` table with status 'pending'
5. **Process Attachments** - Downloads and uploads to Cloud Storage
6. **Update Status** - Sets email status to 'processing'
7. **Mark as Processed** - Uses `EmailService.markAsProcessed()` to label/mark email

### Idempotency

The service checks for existing emails using `app_id + provider_id` unique constraint to prevent duplicate processing.

## Testing

```bash
# Local testing
python main.py

# Test with Gmail
export EMAIL_PROVIDER_TYPE=gmail
export GMAIL_CLIENT_ID=...
export GMAIL_CLIENT_SECRET=...
export GMAIL_REFRESH_TOKEN=...
python main.py
```

## TODO

- [ ] Implement app_id detection from sender email
- [ ] Add IMAP provider support
- [ ] Add SendGrid provider support
- [ ] Add Mailgun provider support
- [ ] Add Microsoft Graph provider support
- [ ] Implement Gmail Push notifications (webhooks)
- [ ] Add unit tests
- [ ] Add integration tests
- [ ] Add error retry logic with exponential backoff
- [ ] Add monitoring and alerting

## Related Documentation

- [Email Ingestion Checklist](../../app/docs/technical-roadmap/checklists/06-email-ingestion-checklist.md)
- [Email Provider Specification](../../app/docs/technical-roadmap/specs/integrations/email-provider-specification.md)
- [Service Interfaces Specification](../../app/docs/technical-roadmap/specs/service-interfaces-specification.md)
