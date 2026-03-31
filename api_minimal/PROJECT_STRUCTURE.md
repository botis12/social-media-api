# Project Structure

This document describes the organization and purpose of files in the Social Media Data Extraction API project.

## Directory Layout

```
social_media_data_api/
├── client/                          # Frontend React application
│   ├── public/                      # Static assets
│   ├── src/
│   │   ├── components/              # Reusable React components
│   │   ├── pages/                   # Page-level components
│   │   ├── lib/                     # Utility functions and helpers
│   │   ├── App.tsx                  # Main app component
│   │   └── main.tsx                 # Entry point
│   └── index.html                   # HTML template
│
├── server/                          # Backend Express.js application
│   ├── _core/                       # Core framework files
│   │   ├── index.ts                 # Server entry point
│   │   ├── context.ts               # tRPC context setup
│   │   ├── oauth.ts                 # OAuth flow handling
│   │   ├── env.ts                   # Environment variables
│   │   └── vite.ts                  # Vite integration
│   │
│   ├── scrapers/                    # Web scraping modules
│   │   └── index.ts                 # Playwright-based scrapers for Reddit, Twitter, LinkedIn
│   │
│   ├── api-routes.ts                # REST API endpoint definitions
│   ├── custom-server.ts             # Custom Express server setup
│   ├── middleware.ts                # Authentication and rate limiting middleware
│   ├── db.ts                        # Database connection and helpers
│   ├── db-helpers.ts                # Database query functions
│   ├── redis-utils.ts               # Redis operations (caching, rate limiting)
│   ├── job-processor.ts             # Bull job queue processor
│   ├── webhook-service.ts           # Webhook delivery and retry logic
│   ├── swagger.ts                   # OpenAPI/Swagger configuration
│   ├── routers.ts                   # tRPC procedure definitions
│   └── auth.logout.test.ts          # Example test file
│
├── drizzle/                         # Database schema and migrations
│   ├── schema.ts                    # Database table definitions
│   └── 0001_*.sql                   # Generated migration files
│
├── storage/                         # S3 storage helpers
│   └── index.ts                     # File upload utilities
│
├── shared/                          # Shared constants and types
│   └── const.ts                     # Shared constants
│
├── .env.example                     # Example environment variables
├── docker-compose.yml               # Docker Compose configuration
├── Dockerfile                       # Docker image definition
├── drizzle.config.ts                # Drizzle ORM configuration
├── package.json                     # Project dependencies
├── tsconfig.json                    # TypeScript configuration
├── vite.config.ts                   # Vite build configuration
├── API_README.md                    # API documentation
├── PROJECT_STRUCTURE.md             # This file
└── todo.md                          # Project tasks and features
```

## Key Files and Their Purpose

### Server Files

**`server/_core/index.ts`**
- Main server entry point
- Initializes Express app
- Registers OAuth routes
- Sets up tRPC middleware
- Integrates custom API routes
- Handles graceful shutdown

**`server/api-routes.ts`**
- Defines REST API endpoints for scraping
- Implements authentication middleware
- Handles job creation and status checking
- Manages API keys and webhooks
- Implements credit deduction logic

**`server/scrapers/index.ts`**
- Playwright-based web scraping engines
- Implements anti-bot bypass mechanisms:
  - User-agent rotation
  - Proxy rotation
  - CAPTCHA detection
  - Headless browser stealth mode
- Provides scrapers for:
  - Reddit (subreddit posts)
  - Twitter/X (tweet search)
  - LinkedIn (company posts)

**`server/job-processor.ts`**
- Bull queue setup for async job processing
- Handles job execution and result storage
- Manages webhook triggers on job completion
- Implements retry logic with exponential backoff

**`server/redis-utils.ts`**
- Rate limiting per API key
- Caching layer for frequently accessed data
- Job queue management
- Session management

**`server/middleware.ts`**
- Bearer token authentication
- Rate limit checking
- Credit balance verification
- Webhook signature validation
- Error handling

**`server/db-helpers.ts`**
- Database query functions for:
  - API keys management
  - Usage credits tracking
  - Job management
  - Posts and comments storage
  - Webhook management

**`server/webhook-service.ts`**
- Webhook delivery with retry logic
- Exponential backoff implementation
- Event logging and tracking
- Signature generation for security

**`server/custom-server.ts`**
- Express app configuration
- Route registration
- Middleware setup
- Webhook processor initialization

**`server/swagger.ts`**
- OpenAPI 3.0 specification
- Swagger UI configuration
- API documentation generation

### Database Files

**`drizzle/schema.ts`**
- Database table definitions using Drizzle ORM
- Tables include:
  - `users`: User accounts
  - `apiKeys`: API key management
  - `usageCredits`: Credit tracking
  - `jobs`: Scraping job records
  - `posts`: Scraped posts
  - `comments`: Scraped comments
  - `webhooks`: Webhook configurations
  - `webhookEvents`: Webhook delivery tracking

### Configuration Files

**`docker-compose.yml`**
- PostgreSQL service
- Redis service
- Node.js application service
- pgAdmin for database management
- Redis Commander for cache management

**`Dockerfile`**
- Multi-stage build for production
- Playwright browser installation
- Health check configuration

**`package.json`**
- Project dependencies
- Build and dev scripts
- Project metadata

**`tsconfig.json`**
- TypeScript compiler configuration
- Path aliases
- Module resolution settings

**`vite.config.ts`**
- Frontend build configuration
- Development server setup
- Plugin configuration

**`drizzle.config.ts`**
- Drizzle ORM configuration
- Database connection settings
- Migration paths

## Data Flow

### Scraping Flow
1. User creates scraping job via REST API endpoint
2. API validates authentication and credits
3. Job is added to Redis queue
4. Job processor picks up job from queue
5. Appropriate scraper (Reddit/Twitter/LinkedIn) is executed
6. Scraped data is stored in PostgreSQL
7. Job status is updated
8. Webhook notification is sent to registered endpoints

### Authentication Flow
1. User generates API key via `/api/keys` endpoint
2. API key is stored in PostgreSQL
3. User includes API key in Authorization header
4. Middleware validates API key
5. Rate limit is checked against Redis
6. Request is processed
7. Credits are deducted if applicable

### Rate Limiting Flow
1. Request arrives with API key
2. Middleware checks Redis for current request count
3. If count < limit, request is allowed
4. Counter is incremented in Redis
5. TTL is set to 60 seconds
6. If count >= limit, 429 error is returned

### Webhook Flow
1. Job completes or fails
2. Webhook event is created in database
3. Webhook processor picks up pending events
4. Payload is signed with HMAC-SHA256
5. HTTP POST is sent to webhook URL
6. If delivery fails, event is retried with exponential backoff
7. After max retries, event is marked as failed

## Environment Variables

See `.env.example` for complete list of environment variables. Key variables:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`: Redis configuration
- `NODE_ENV`: Environment (development/production)
- `PORT`: Server port
- `API_URL`: Public API URL for documentation
- `PROXY_LIST`: Comma-separated proxy URLs for scraping

## Running the Project

### Development
```bash
pnpm install
pnpm dev
```

### Production
```bash
pnpm install
pnpm build
pnpm start
```

### Docker
```bash
docker-compose up -d
```

## Testing

Run tests with:
```bash
pnpm test
```

Tests are located in `server/*.test.ts` files.

## Deployment

The project can be deployed to:
- Docker containers (using provided Dockerfile)
- Traditional servers (Node.js + PostgreSQL + Redis)
- Cloud platforms (AWS, GCP, Azure, etc.)

See `API_README.md` for deployment instructions.

## Performance Considerations

1. **Database Indexing**: Ensure indexes on frequently queried columns
2. **Redis Memory**: Monitor Redis memory usage for caching
3. **Job Queue**: Adjust job concurrency based on server resources
4. **Proxy Rotation**: Use residential proxies for better success rates
5. **Rate Limiting**: Configure per-user limits based on usage patterns

## Security Considerations

1. **API Keys**: Store securely, never commit to version control
2. **Webhook Signatures**: Always verify webhook signatures
3. **Database**: Use strong passwords and enable SSL/TLS
4. **Redis**: Set password and disable public access
5. **Proxy Credentials**: Store securely in environment variables
6. **CORS**: Configure appropriately for your domain
