import { eq, and, desc } from 'drizzle-orm';
import { getDb } from './db';
import {
  apiKeys,
  jobs,
  posts,
  comments,
  usageCredits,
  webhooks,
  webhookEvents,
  InsertApiKey,
  InsertJob,
  InsertPost,
  InsertComment,
  InsertWebhook,
  InsertWebhookEvent,
  Job,
  Post,
  ApiKey,
  UsageCredit,
} from '../drizzle/schema';
import { nanoid } from 'nanoid';
import crypto from 'crypto';

// ============ API Keys ============
export async function createApiKey(userId: number, name: string, rateLimit: number = 100): Promise<ApiKey> {
  const db = await getDb();
  if (!db) throw new Error('Database not available');

  const key = `sk_${nanoid(32)}`;
  const result = await db.insert(apiKeys).values({
    userId,
    key,
    name,
    rateLimit,
  });

  return {
    id: (result as any).insertId,
    userId,
    key,
    name,
    isActive: true,
    rateLimit,
    createdAt: new Date(),
    updatedAt: new Date(),
    lastUsedAt: null,
  };
}

export async function getApiKey(key: string): Promise<ApiKey | null> {
  const db = await getDb();
  if (!db) return null;

  const result = await db.select().from(apiKeys).where(eq(apiKeys.key, key)).limit(1);
  return result.length > 0 ? result[0] : null;
}

export async function getUserApiKeys(userId: number): Promise<ApiKey[]> {
  const db = await getDb();
  if (!db) return [];

  return db.select().from(apiKeys).where(eq(apiKeys.userId, userId));
}

export async function deactivateApiKey(keyId: number): Promise<void> {
  const db = await getDb();
  if (!db) return;

  await db.update(apiKeys).set({ isActive: false }).where(eq(apiKeys.id, keyId));
}

// ============ Usage Credits ============
export async function getUserCredits(userId: number): Promise<UsageCredit | null> {
  const db = await getDb();
  if (!db) return null;

  const result = await db.select().from(usageCredits).where(eq(usageCredits.userId, userId)).limit(1);
  return result.length > 0 ? result[0] : null;
}

export async function initializeCredits(userId: number, initialBalance: string = '100.00'): Promise<UsageCredit> {
  const db = await getDb();
  if (!db) throw new Error('Database not available');

  const existing = await getUserCredits(userId);
  if (existing) return existing;

  const result = await db.insert(usageCredits).values({
    userId,
    balance: initialBalance,
    totalUsed: '0',
  });

  return {
    id: (result as any).insertId,
    userId,
    balance: initialBalance,
    totalUsed: '0',
    createdAt: new Date(),
    updatedAt: new Date(),
  };
}

export async function deductCredits(userId: number, amount: string): Promise<boolean> {
  const db = await getDb();
  if (!db) return false;

  const credits = await getUserCredits(userId);
  if (!credits) return false;

  const newBalance = (parseFloat(credits.balance) - parseFloat(amount)).toFixed(2);
  if (parseFloat(newBalance) < 0) return false;

  await db
    .update(usageCredits)
    .set({
      balance: newBalance,
      totalUsed: (parseFloat(credits.totalUsed) + parseFloat(amount)).toFixed(2),
    })
    .where(eq(usageCredits.userId, userId));

  return true;
}

export async function addCredits(userId: number, amount: string): Promise<void> {
  const db = await getDb();
  if (!db) return;

  const credits = await getUserCredits(userId);
  if (!credits) {
    await initializeCredits(userId, amount);
    return;
  }

  const newBalance = (parseFloat(credits.balance) + parseFloat(amount)).toFixed(2);
  await db.update(usageCredits).set({ balance: newBalance }).where(eq(usageCredits.userId, userId));
}

// ============ Jobs ============
export async function createJob(
  userId: number,
  apiKeyId: number,
  platform: 'reddit' | 'twitter' | 'linkedin',
  jobType: 'posts' | 'search' | 'company_posts',
  query: string,
  creditsCost: string
): Promise<Job> {
  const db = await getDb();
  if (!db) throw new Error('Database not available');

  const jobId = `job_${nanoid(16)}`;
  await db.insert(jobs).values({
    id: jobId,
    userId,
    apiKeyId,
    platform,
    jobType,
    query,
    creditsCost,
  });

  return {
    id: jobId,
    userId,
    apiKeyId,
    platform,
    jobType,
    query,
    status: 'pending',
    progress: 0,
    resultCount: 0,
    creditsCost,
    error: null,
    createdAt: new Date(),
    updatedAt: new Date(),
    completedAt: null,
  };
}

export async function getJob(jobId: string): Promise<Job | null> {
  const db = await getDb();
  if (!db) return null;

  const result = await db.select().from(jobs).where(eq(jobs.id, jobId)).limit(1);
  return result.length > 0 ? result[0] : null;
}

export async function updateJobStatus(
  jobId: string,
  status: 'pending' | 'processing' | 'completed' | 'failed',
  progress?: number,
  resultCount?: number,
  error?: string
): Promise<void> {
  const db = await getDb();
  if (!db) return;

  const updates: any = { status };
  if (progress !== undefined) updates.progress = progress;
  if (resultCount !== undefined) updates.resultCount = resultCount;
  if (error !== undefined) updates.error = error;
  if (status === 'completed') updates.completedAt = new Date();

  await db.update(jobs).set(updates).where(eq(jobs.id, jobId));
}

export async function getUserJobs(userId: number, limit: number = 50): Promise<Job[]> {
  const db = await getDb();
  if (!db) return [];

  return db
    .select()
    .from(jobs)
    .where(eq(jobs.userId, userId))
    .orderBy(desc(jobs.createdAt))
    .limit(limit);
}

// ============ Posts ============
export async function savePosts(postsData: InsertPost[]): Promise<void> {
  const db = await getDb();
  if (!db) return;

  if (postsData.length === 0) return;
  await db.insert(posts).values(postsData);
}

export async function getJobPosts(jobId: string, limit: number = 100, offset: number = 0): Promise<Post[]> {
  const db = await getDb();
  if (!db) return [];

  return db
    .select()
    .from(posts)
    .where(eq(posts.jobId, jobId))
    .limit(limit)
    .offset(offset);
}

// ============ Comments ============
export async function saveComments(commentsData: InsertComment[]): Promise<void> {
  const db = await getDb();
  if (!db) return;

  if (commentsData.length === 0) return;
  await db.insert(comments).values(commentsData);
}

// ============ Webhooks ============
export async function createWebhook(
  userId: number,
  url: string,
  events: string[]
): Promise<{ id: number; secret: string }> {
  const db = await getDb();
  if (!db) throw new Error('Database not available');

  const secret = crypto.randomBytes(32).toString('hex');
  const result = await db.insert(webhooks).values({
    userId,
    url,
    events: JSON.stringify(events),
    secret,
  });

  return {
    id: (result as any).insertId,
    secret,
  };
}

export async function getUserWebhooks(userId: number): Promise<any[]> {
  const db = await getDb();
  if (!db) return [];

  const result = await db.select().from(webhooks).where(eq(webhooks.userId, userId));
  return result.map(w => ({
    ...w,
    events: typeof w.events === 'string' ? JSON.parse(w.events) : w.events,
  }));
}

export async function triggerWebhook(webhookId: number, jobId: string, event: string, payload: any): Promise<void> {
  const db = await getDb();
  if (!db) return;

  await db.insert(webhookEvents).values({
    webhookId,
    jobId,
    event,
    payload: JSON.stringify(payload),
  });
}

export async function getPendingWebhookEvents(limit: number = 10): Promise<any[]> {
  const db = await getDb();
  if (!db) return [];

  const result = await db
    .select()
    .from(webhookEvents)
    .where(eq(webhookEvents.status, 'pending'))
    .limit(limit);

  return result.map(e => ({
    ...e,
    payload: typeof e.payload === 'string' ? JSON.parse(e.payload) : e.payload,
  }));
}

export async function updateWebhookEventStatus(
  eventId: number,
  status: 'pending' | 'sent' | 'failed',
  attempts?: number
): Promise<void> {
  const db = await getDb();
  if (!db) return;

  const updates: any = { status };
  if (attempts !== undefined) updates.attempts = attempts;
  if (status !== 'pending') updates.lastAttemptAt = new Date();

  await db.update(webhookEvents).set(updates).where(eq(webhookEvents.id, eventId));
}
