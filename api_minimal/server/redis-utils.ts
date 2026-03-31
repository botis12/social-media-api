import Redis from 'ioredis';

const redis = new Redis({
  host: process.env.REDIS_HOST || 'localhost',
  port: parseInt(process.env.REDIS_PORT || '6379'),
  password: process.env.REDIS_PASSWORD,
  retryStrategy: (times) => Math.min(times * 50, 2000),
});

redis.on('error', (err) => console.error('Redis error:', err));
redis.on('connect', () => console.log('Redis connected'));

// ============ Rate Limiting ============
export async function checkRateLimit(apiKeyId: number, limit: number): Promise<boolean> {
  const key = `rate_limit:${apiKeyId}`;
  const current = await redis.incr(key);

  if (current === 1) {
    // Set expiry on first request (1 minute window)
    await redis.expire(key, 60);
  }

  return current <= limit;
}

export async function getRateLimitStatus(apiKeyId: number): Promise<{ current: number; limit: number; resetAt: number }> {
  const key = `rate_limit:${apiKeyId}`;
  const current = parseInt((await redis.get(key)) || '0');
  const ttl = await redis.ttl(key);

  return {
    current,
    limit: 100, // Default limit
    resetAt: ttl > 0 ? Date.now() + ttl * 1000 : Date.now(),
  };
}

// ============ Caching ============
export async function getCache<T>(key: string): Promise<T | null> {
  const data = await redis.get(`cache:${key}`);
  if (!data) return null;

  try {
    return JSON.parse(data) as T;
  } catch {
    return null;
  }
}

export async function setCache<T>(key: string, data: T, ttl: number = 3600): Promise<void> {
  await redis.setex(`cache:${key}`, ttl, JSON.stringify(data));
}

export async function invalidateCache(pattern: string): Promise<void> {
  const keys = await redis.keys(`cache:${pattern}`);
  if (keys.length > 0) {
    await redis.del(...keys);
  }
}

// ============ Job Queue ============
export async function enqueueJob(jobId: string, jobData: any): Promise<void> {
  await redis.lpush('job_queue', JSON.stringify({ jobId, ...jobData }));
}

export async function dequeueJob(): Promise<any | null> {
  const data = await redis.rpop('job_queue');
  if (!data) return null;

  try {
    return JSON.parse(data);
  } catch {
    return null;
  }
}

export async function getJobQueueLength(): Promise<number> {
  return redis.llen('job_queue');
}

// ============ Job Status ============
export async function setJobStatus(jobId: string, status: string): Promise<void> {
  await redis.set(`job_status:${jobId}`, status, 'EX', 86400); // 24 hours
}

export async function getJobStatus(jobId: string): Promise<string | null> {
  return redis.get(`job_status:${jobId}`);
}

// ============ Session Management ============
export async function setSession(sessionId: string, data: any, ttl: number = 3600): Promise<void> {
  await redis.setex(`session:${sessionId}`, ttl, JSON.stringify(data));
}

export async function getSession(sessionId: string): Promise<any | null> {
  const data = await redis.get(`session:${sessionId}`);
  if (!data) return null;

  try {
    return JSON.parse(data);
  } catch {
    return null;
  }
}

export async function deleteSession(sessionId: string): Promise<void> {
  await redis.del(`session:${sessionId}`);
}

export async function closeRedis(): Promise<void> {
  await redis.quit();
}

export default redis;
