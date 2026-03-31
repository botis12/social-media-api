# Social Media Data Extraction API - TODO

## Database & Schema
- [x] Define Drizzle ORM schema for api_keys, jobs, posts, comments, users, usage_credits, webhooks
- [x] Generate and apply database migrations
- [x] Create indexes for efficient querying

## Scraping Engines
- [x] Implement Reddit scraper with Playwright (posts, comments, user metadata)
- [x] Implement Twitter/X scraper with Playwright (tweets, user info, engagement metrics)
- [x] Implement LinkedIn scraper with Playwright (company posts, engagement data)
- [x] Add anti-bot bypass mechanisms (user-agent rotation, CAPTCHA handling, proxy rotation)
- [x] Add retry logic with exponential backoff

## REST API Endpoints
- [x] GET /api/reddit/{subreddit}/posts - fetch posts from subreddit
- [x] GET /api/twitter/search - search tweets by keyword/hashtag
- [x] GET /api/linkedin/company/{name}/posts - fetch company posts
- [x] POST /api/jobs - create async scraping job
- [x] GET /api/jobs/{id}/status - check job status and results
- [x] GET /api/jobs/{id}/results - retrieve job results with pagination

## Authentication & API Key Management
- [x] Implement Bearer token authentication middleware
- [x] Create API key generation and management endpoints
- [x] Add API key validation and scope checking
- [x] Implement API key revocation

## Rate Limiting & Caching
- [x] Integrate Redis for rate limiting per API key
- [x] Implement configurable rate limits (requests per minute/hour)
- [x] Add Redis caching layer for frequently accessed data
- [x] Implement cache invalidation strategies

## Credit-Based Usage Tracking
- [x] Design credit system (cost per request type)
- [x] Implement credit deduction on API calls
- [x] Create credit balance monitoring endpoints
- [x] Add low-balance alerts and warnings

## Job Queue System
- [x] Implement async job queue using Bull or similar
- [x] Add job status tracking (pending, processing, completed, failed)
- [x] Implement job result storage and retrieval
- [x] Add job timeout and retry mechanisms

## Webhook Notifications
- [x] Implement webhook registration endpoints
- [x] Add webhook payload signing for security
- [x] Implement webhook retry logic with exponential backoff
- [x] Create webhook event logging and monitoring

## Documentation & Testing
- [x] Generate OpenAPI/Swagger documentation
- [x] Write unit tests for scrapers
- [x] Write integration tests for API endpoints
- [x] Write tests for rate limiting and credit system
- [x] Create comprehensive README with setup instructions

## Deployment
- [x] Create Docker and docker-compose configuration
- [x] Set up environment variable management
- [x] Create health check endpoints
- [x] Implement graceful shutdown handling
