# Setup and Deployment Guide

This guide provides step-by-step instructions for setting up and deploying the Social Media Data Extraction API.

## Local Development Setup

### Prerequisites

- Node.js 18 or higher
- PostgreSQL 12 or higher
- Redis 6 or higher
- Git

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd social_media_data_api
```

### Step 2: Install Dependencies

```bash
pnpm install
```

### Step 3: Configure Environment Variables

Copy the example environment file and update with your settings:

```bash
cp .env.example .env
```

Edit `.env` with your database and Redis credentials:

```env
DATABASE_URL=mysql://user:password@localhost:3306/social_media_api
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
NODE_ENV=development
PORT=3000
```

### Step 4: Setup Database

Generate and apply migrations:

```bash
pnpm drizzle-kit generate
pnpm drizzle-kit migrate
```

### Step 5: Start Development Server

```bash
pnpm dev
```

The server will start on `http://localhost:3000` and API documentation will be available at `http://localhost:3000/api-docs`.

## Docker Deployment

### Prerequisites

- Docker
- Docker Compose

### Step 1: Build and Start Services

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database
- Redis cache
- Node.js application
- pgAdmin (database management UI at http://localhost:5050)
- Redis Commander (cache management UI at http://localhost:8081)

### Step 2: Initialize Database

```bash
docker-compose exec app pnpm drizzle-kit migrate
```

### Step 3: Verify Services

Check that all services are running:

```bash
docker-compose ps
```

Access the API at `http://localhost:3000/api-docs`.

## Production Deployment

### Environment Variables

Set these environment variables in your production environment:

```env
NODE_ENV=production
DATABASE_URL=mysql://prod_user:prod_password@prod_host:3306/social_media_api
REDIS_HOST=redis.prod.internal
REDIS_PASSWORD=secure_redis_password
API_URL=https://api.yourdomain.com
PORT=3000
```

### Build for Production

```bash
pnpm build
```

### Start Production Server

```bash
pnpm start
```

### Health Check

Verify the server is running:

```bash
curl http://localhost:3000/health
```

## AWS Deployment

### Using Elastic Container Service (ECS)

1. Push Docker image to ECR:

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker build -t social-media-api .
docker tag social-media-api:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/social-media-api:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/social-media-api:latest
```

2. Create ECS task definition with:
   - Docker image from ECR
   - Environment variables
   - Port mapping (3000)
   - CloudWatch logging

3. Create ECS service with:
   - Load balancer (ALB)
   - Auto-scaling policy
   - Health check endpoint

### Using RDS for Database

1. Create RDS MySQL instance
2. Update `DATABASE_URL` to point to RDS endpoint
3. Run migrations:

```bash
pnpm drizzle-kit migrate
```

### Using ElastiCache for Redis

1. Create ElastiCache Redis cluster
2. Update `REDIS_HOST` and `REDIS_PASSWORD` environment variables
3. Ensure security groups allow communication

## Kubernetes Deployment

### Create Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: social-media-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: social-media-api
  template:
    metadata:
      labels:
        app: social-media-api
    spec:
      containers:
      - name: api
        image: <registry>/social-media-api:latest
        ports:
        - containerPort: 3000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: database-url
        - name: REDIS_HOST
          valueFrom:
            configMapKeyRef:
              name: api-config
              key: redis-host
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 10
          periodSeconds: 5
```

### Deploy to Kubernetes

```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

## Monitoring and Logging

### Application Logs

View logs:

```bash
# Docker
docker-compose logs -f app

# Kubernetes
kubectl logs -f deployment/social-media-api
```

### Health Monitoring

Monitor application health:

```bash
curl http://localhost:3000/health
curl http://localhost:3000/api/stats
```

### Database Monitoring

Monitor database performance:

```bash
# PostgreSQL
SELECT * FROM pg_stat_statements;
SELECT * FROM pg_stat_activity;
```

### Redis Monitoring

Monitor Redis:

```bash
redis-cli INFO
redis-cli MONITOR
```

## Backup and Recovery

### Database Backup

```bash
# PostgreSQL
pg_dump -U user -h localhost social_media_api > backup.sql

# Restore
psql -U user -h localhost social_media_api < backup.sql
```

### Redis Backup

```bash
# Create backup
redis-cli BGSAVE

# Copy dump.rdb to safe location
cp /var/lib/redis/dump.rdb /backup/redis_backup.rdb
```

## Scaling

### Horizontal Scaling

1. Deploy multiple instances behind a load balancer
2. Use shared PostgreSQL and Redis instances
3. Configure sticky sessions if needed

### Vertical Scaling

1. Increase server resources (CPU, memory)
2. Adjust job concurrency in environment variables
3. Monitor performance metrics

## Troubleshooting

### Database Connection Issues

```bash
# Test connection
mysql -u user -p -h host database_name

# Check environment variables
echo $DATABASE_URL
```

### Redis Connection Issues

```bash
# Test connection
redis-cli -h localhost -p 6379 ping

# Check environment variables
echo $REDIS_HOST $REDIS_PORT
```

### Job Queue Issues

Check job queue status:

```bash
curl http://localhost:3000/api/stats
```

### Rate Limiting Issues

Check rate limit status:

```bash
# Via Redis
redis-cli GET rate_limit:1
```

## Performance Optimization

### Database Optimization

1. Ensure indexes are created (see `drizzle/0002_add_indexes.sql`)
2. Monitor slow queries
3. Optimize query patterns

### Redis Optimization

1. Set appropriate memory limits
2. Configure eviction policy
3. Monitor memory usage

### Application Optimization

1. Adjust job concurrency based on resources
2. Implement caching strategies
3. Monitor response times

## Security Checklist

- [ ] Change default passwords
- [ ] Enable SSL/TLS for database connections
- [ ] Enable SSL/TLS for Redis connections
- [ ] Use environment variables for secrets
- [ ] Implement API rate limiting
- [ ] Enable CORS appropriately
- [ ] Validate all user inputs
- [ ] Implement request signing for webhooks
- [ ] Monitor for suspicious activity
- [ ] Regular security updates

## Support

For issues or questions, please refer to the API documentation at `/api-docs` or contact support.
