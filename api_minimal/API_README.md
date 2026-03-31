# Social Media Data Extraction API

A production-ready API service for extracting structured, cleaned data from restricted social media platforms (Reddit, Twitter/X, LinkedIn) with anti-bot bypass mechanisms, rate limiting, and credit-based usage tracking.

## Features

- **Multi-Platform Scraping**: Extract posts, comments, and user metadata from Reddit, Twitter, and LinkedIn
- **Anti-Bot Bypass**: User-agent rotation, CAPTCHA handling, proxy rotation, and headless browser stealth mode
- **Async Job Queue**: Non-blocking scraping with job status tracking and result retrieval
- **Rate Limiting**: Configurable per-API-key rate limits with Redis-backed enforcement
- **Credit System**: Pay-per-use model with credit deduction and balance monitoring
- **Webhook Support**: Real-time notifications for job completion and failures with retry logic
- **API Key Management**: Secure Bearer token authentication with key generation and revocation
- **Caching Layer**: Redis-based caching for frequently accessed data
- **OpenAPI Documentation**: Auto-generated Swagger UI for all endpoints
- **Database Persistence**: PostgreSQL with Drizzle ORM for reliable data storage

## Tech Stack

- **Backend**: Express.js + Node.js
- **Scraping**: Playwright (headless browser automation)
- **Job Queue**: Bull (Redis-backed job processing)
- **Caching & Rate Limiting**: Redis + ioredis
- **Database**: PostgreSQL with Drizzle ORM
- **API Documentation**: Swagger/OpenAPI 3.0
- **Authentication**: Bearer token (API keys)

## Prerequisites

- Node.js 18+
- PostgreSQL 12+
- Redis 6+
- Playwright browsers (automatically installed)

## Installation

### 1. Clone and Install Dependencies

```bash
cd social_media_data_api
pnpm install
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=mysql://user:password@localhost:3306/social_media_api

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# API Configuration
API_URL=http://localhost:3000
NODE_ENV=development
PORT=3000

# Optional: Proxy Configuration
PROXY_LIST=http://proxy1:8080,http://proxy2:8080

# Optional: CAPTCHA Solving Service
CAPTCHA_API_KEY=your_captcha_service_key
```

### 3. Database Setup

Generate and apply migrations:

```bash
pnpm drizzle-kit generate
pnpm drizzle-kit migrate
```

### 4. Start the Server

```bash
# Development
pnpm dev

# Production
pnpm build
pnpm start
```

The server will start on `http://localhost:3000` and API documentation will be available at `http://localhost:3000/api-docs`.

## API Endpoints

### Authentication

All endpoints require a Bearer token in the Authorization header:

```
Authorization: Bearer sk_your_api_key_here
```

### API Key Management

#### Create API Key
```
POST /api/keys
Content-Type: application/json

{
  "name": "My Scraper",
  "rateLimit": 100
}
```

**Response:**
```json
{
  "id": 1,
  "key": "sk_abc123def456",
  "name": "My Scraper",
  "rateLimit": 100,
  "createdAt": "2026-03-31T10:00:00Z"
}
```

#### List API Keys
```
GET /api/keys
```

### Credits Management

#### Get Credit Balance
```
GET /api/credits
```

**Response:**
```json
{
  "balance": "95.50",
  "totalUsed": "4.50",
  "updatedAt": "2026-03-31T10:00:00Z"
}
```

### Scraping Endpoints

#### Reddit: Get Subreddit Posts
```
POST /api/reddit/{subreddit}/posts
Content-Type: application/json

{
  "limit": 25
}
```

**Response:**
```json
{
  "jobId": "job_abc123def456",
  "status": "pending",
  "createdAt": "2026-03-31T10:00:00Z"
}
```

#### Twitter: Search Tweets
```
POST /api/twitter/search
Content-Type: application/json

{
  "query": "#nodejs",
  "limit": 25
}
```

**Response:**
```json
{
  "jobId": "job_abc123def456",
  "status": "pending",
  "createdAt": "2026-03-31T10:00:00Z"
}
```

#### LinkedIn: Get Company Posts
```
POST /api/linkedin/company/{name}/posts
Content-Type: application/json

{
  "limit": 25
}
```

**Response:**
```json
{
  "jobId": "job_abc123def456",
  "status": "pending",
  "createdAt": "2026-03-31T10:00:00Z"
}
```

### Job Management

#### Create Generic Scraping Job
```
POST /api/jobs
Content-Type: application/json

{
  "platform": "reddit|twitter|linkedin",
  "jobType": "posts|search|company_posts",
  "query": "nodejs",
  "limit": 25
}
```

#### Get Job Status
```
GET /api/jobs/{jobId}
```

**Response:**
```json
{
  "id": "job_abc123def456",
  "platform": "reddit",
  "jobType": "posts",
  "query": "nodejs",
  "status": "processing",
  "progress": 45,
  "resultCount": 0,
  "error": null,
  "createdAt": "2026-03-31T10:00:00Z",
  "completedAt": null
}
```

#### Get Job Results
```
GET /api/jobs/{jobId}/results?limit=50&offset=0
```

**Response:**
```json
{
  "jobId": "job_abc123def456",
  "totalResults": 25,
  "limit": 50,
  "offset": 0,
  "results": [
    {
      "id": "post_123",
      "platform": "reddit",
      "author": "username",
      "title": "Post Title",
      "content": "Post content...",
      "url": "https://reddit.com/r/nodejs/...",
      "likes": 150,
      "comments": 25,
      "shares": 5,
      "postedAt": "2026-03-31T09:00:00Z"
    }
  ]
}
```

#### List User Jobs
```
GET /api/jobs?limit=50
```

### Webhook Management

#### Register Webhook
```
POST /api/webhooks
Content-Type: application/json

{
  "url": "https://your-domain.com/webhook",
  "events": ["job.completed", "job.failed"]
}
```

**Response:**
```json
{
  "id": 1,
  "secret": "whsec_abc123def456",
  "createdAt": "2026-03-31T10:00:00Z"
}
```

#### List Webhooks
```
GET /api/webhooks
```

### System Endpoints

#### Health Check
```
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2026-03-31T10:00:00Z"
}
```

#### Queue Statistics
```
GET /api/stats
```

**Response:**
```json
{
  "queue": {
    "active": 2,
    "completed": 150,
    "failed": 3,
    "delayed": 0,
    "waiting": 5
  },
  "timestamp": "2026-03-31T10:00:00Z"
}
```

## Error Handling

The API returns standard HTTP status codes:

- `200 OK`: Successful request
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Missing or invalid API key
- `402 Payment Required`: Insufficient credits
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

**Error Response Format:**
```json
{
  "error": "Error message describing what went wrong"
}
```

## Credit Costs

- Reddit posts scraping: 5 credits
- Twitter search: 5 credits
- LinkedIn company posts: 5 credits

## Rate Limiting

Rate limits are applied per API key and are configurable. Default: 100 requests per minute.

The rate limit status is returned in response headers:
- `X-RateLimit-Limit`: Maximum requests per minute
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Unix timestamp when limit resets

## Webhook Events

### Job Completed Event
```json
{
  "event": "job.completed",
  "jobId": "job_abc123def456",
  "platform": "reddit",
  "resultCount": 25,
  "completedAt": "2026-03-31T10:05:00Z"
}
```

### Job Failed Event
```json
{
  "event": "job.failed",
  "jobId": "job_abc123def456",
  "platform": "reddit",
  "error": "Failed to scrape subreddit",
  "failedAt": "2026-03-31T10:05:00Z"
}
```

Webhook payloads are signed with HMAC-SHA256. Verify the signature using the webhook secret:

```javascript
const crypto = require('crypto');
const payload = JSON.stringify(req.body);
const signature = crypto.createHmac('sha256', webhookSecret).update(payload).digest('hex');
const isValid = signature === req.headers['x-webhook-signature'];
```

## Best Practices

1. **Store API Keys Securely**: Never commit API keys to version control
2. **Monitor Credit Balance**: Implement alerts when balance is low
3. **Use Webhooks**: Instead of polling, use webhooks for job completion notifications
4. **Implement Backoff**: Use exponential backoff when retrying failed requests
5. **Cache Results**: Store scraped data locally to avoid re-scraping
6. **Rate Limit Awareness**: Monitor rate limit headers and adjust request frequency
7. **Error Handling**: Implement proper error handling for failed jobs

## Deployment

### Docker Deployment

```bash
docker-compose up -d
```

See `docker-compose.yml` for configuration details.

### Environment Variables for Production

```env
NODE_ENV=production
DATABASE_URL=mysql://prod_user:prod_password@prod_host:3306/social_media_api
REDIS_HOST=redis.prod.internal
REDIS_PASSWORD=secure_redis_password
API_URL=https://api.yourdomain.com
```

## Monitoring

Monitor the following metrics:

- Job queue length: `/api/stats`
- Failed jobs: Check webhook delivery logs
- API response times: Monitor `/api/trpc` endpoints
- Database connection pool: Check PostgreSQL metrics
- Redis memory usage: Monitor Redis server

## Troubleshooting

### Jobs Stuck in Processing

Check the job processor worker logs and ensure Redis and PostgreSQL are accessible.

### Rate Limit Errors

Verify your API key's rate limit configuration and implement request queuing on the client side.

### Webhook Delivery Failures

Check webhook event logs in the database and verify the webhook URL is accessible from the server.

### CAPTCHA Detection

If CAPTCHA is detected, the scraper will wait 5 seconds. For production, integrate with a CAPTCHA solving service.

## Support

For issues and feature requests, please contact support or open an issue in the repository.

## License

MIT
