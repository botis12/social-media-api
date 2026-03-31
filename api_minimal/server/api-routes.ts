import { Router, Response } from 'express';
import { AuthenticatedRequest, authenticateApiKey, checkRateLimitMiddleware, checkCreditsMiddleware } from './middleware';
import {
  createJob,
  getJob,
  getUserJobs,
  deductCredits,
  getUserCredits,
  getJobPosts,
  createApiKey,
  getUserApiKeys,
  createWebhook,
  getUserWebhooks,
} from './db-helpers';
import { addScrapeJob } from './job-processor';
import { nanoid } from 'nanoid';

const router = Router();

// ============ Authentication Routes ============
router.post('/api/keys', authenticateApiKey, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { name, rateLimit } = req.body;

    if (!name) {
      return res.status(400).json({ error: 'Name is required' });
    }

    const apiKey = await createApiKey(req.userId!, name, rateLimit || 100);

    res.json({
      id: apiKey.id,
      key: apiKey.key,
      name: apiKey.name,
      rateLimit: apiKey.rateLimit,
      createdAt: apiKey.createdAt,
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to create API key' });
  }
});

router.get('/api/keys', authenticateApiKey, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const keys = await getUserApiKeys(req.userId!);

    res.json(
      keys.map((k) => ({
        id: k.id,
        name: k.name,
        rateLimit: k.rateLimit,
        isActive: k.isActive,
        lastUsedAt: k.lastUsedAt,
        createdAt: k.createdAt,
      }))
    );
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch API keys' });
  }
});

// ============ Credits Routes ============
router.get('/api/credits', authenticateApiKey, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const credits = await getUserCredits(req.userId!);

    if (!credits) {
      return res.status(404).json({ error: 'No credits found' });
    }

    res.json({
      balance: credits.balance,
      totalUsed: credits.totalUsed,
      updatedAt: credits.updatedAt,
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch credits' });
  }
});

// ============ Reddit Scraping Routes ============
router.post(
  '/api/reddit/:subreddit/posts',
  authenticateApiKey,
  checkRateLimitMiddleware,
  checkCreditsMiddleware(5),
  async (req: AuthenticatedRequest, res: Response) => {
    try {
      const { subreddit } = req.params;
      const { limit = 25 } = req.body;

      const creditsCost = '5.00';
      const jobId = `job_${nanoid(16)}`;

      // Deduct credits
      const deducted = await deductCredits(req.userId!, creditsCost);
      if (!deducted) {
        return res.status(402).json({ error: 'Insufficient credits' });
      }

      // Create job
      const job = await createJob(
        req.userId!,
        req.apiKeyId!,
        'reddit',
        'posts',
        subreddit,
        creditsCost
      );

      // Add to job queue
      await addScrapeJob(jobId, 'reddit', 'posts', subreddit, req.userId!, limit);

      res.json({
        jobId: job.id,
        status: job.status,
        createdAt: job.createdAt,
      });
    } catch (error) {
      res.status(500).json({ error: 'Failed to create scraping job' });
    }
  }
);

// ============ Twitter Scraping Routes ============
router.post(
  '/api/twitter/search',
  authenticateApiKey,
  checkRateLimitMiddleware,
  checkCreditsMiddleware(5),
  async (req: AuthenticatedRequest, res: Response) => {
    try {
      const { query, limit = 25 } = req.body;

      if (!query) {
        return res.status(400).json({ error: 'Query is required' });
      }

      const creditsCost = '5.00';
      const jobId = `job_${nanoid(16)}`;

      // Deduct credits
      const deducted = await deductCredits(req.userId!, creditsCost);
      if (!deducted) {
        return res.status(402).json({ error: 'Insufficient credits' });
      }

      // Create job
      const job = await createJob(
        req.userId!,
        req.apiKeyId!,
        'twitter',
        'search',
        query,
        creditsCost
      );

      // Add to job queue
      await addScrapeJob(jobId, 'twitter', 'search', query, req.userId!, limit);

      res.json({
        jobId: job.id,
        status: job.status,
        createdAt: job.createdAt,
      });
    } catch (error) {
      res.status(500).json({ error: 'Failed to create scraping job' });
    }
  }
);

// ============ LinkedIn Scraping Routes ============
router.post(
  '/api/linkedin/company/:name/posts',
  authenticateApiKey,
  checkRateLimitMiddleware,
  checkCreditsMiddleware(5),
  async (req: AuthenticatedRequest, res: Response) => {
    try {
      const { name } = req.params;
      const { limit = 25 } = req.body;

      const creditsCost = '5.00';
      const jobId = `job_${nanoid(16)}`;

      // Deduct credits
      const deducted = await deductCredits(req.userId!, creditsCost);
      if (!deducted) {
        return res.status(402).json({ error: 'Insufficient credits' });
      }

      // Create job
      const job = await createJob(
        req.userId!,
        req.apiKeyId!,
        'linkedin',
        'company_posts',
        name,
        creditsCost
      );

      // Add to job queue
      await addScrapeJob(jobId, 'linkedin', 'company_posts', name, req.userId!, limit);

      res.json({
        jobId: job.id,
        status: job.status,
        createdAt: job.createdAt,
      });
    } catch (error) {
      res.status(500).json({ error: 'Failed to create scraping job' });
    }
  }
);

// ============ Job Management Routes ============
router.post(
  '/api/jobs',
  authenticateApiKey,
  checkRateLimitMiddleware,
  async (req: AuthenticatedRequest, res: Response) => {
    try {
      const { platform, jobType, query, limit = 25 } = req.body;

      if (!platform || !jobType || !query) {
        return res.status(400).json({ error: 'platform, jobType, and query are required' });
      }

      const creditsCost = '5.00';
      const jobId = `job_${nanoid(16)}`;

      // Deduct credits
      const deducted = await deductCredits(req.userId!, creditsCost);
      if (!deducted) {
        return res.status(402).json({ error: 'Insufficient credits' });
      }

      // Create job
      const job = await createJob(
        req.userId!,
        req.apiKeyId!,
        platform as 'reddit' | 'twitter' | 'linkedin',
        jobType as 'posts' | 'search' | 'company_posts',
        query,
        creditsCost
      );

      // Add to job queue
      await addScrapeJob(jobId, platform, jobType, query, req.userId!, limit);

      res.json({
        jobId: job.id,
        status: job.status,
        createdAt: job.createdAt,
      });
    } catch (error) {
      res.status(500).json({ error: 'Failed to create job' });
    }
  }
);

router.get('/api/jobs/:jobId', authenticateApiKey, checkRateLimitMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { jobId } = req.params;

    const job = await getJob(jobId);

    if (!job || job.userId !== req.userId) {
      return res.status(404).json({ error: 'Job not found' });
    }

    res.json({
      id: job.id,
      platform: job.platform,
      jobType: job.jobType,
      query: job.query,
      status: job.status,
      progress: job.progress,
      resultCount: job.resultCount,
      error: job.error,
      createdAt: job.createdAt,
      completedAt: job.completedAt,
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch job' });
  }
});

router.get('/api/jobs/:jobId/results', authenticateApiKey, checkRateLimitMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { jobId } = req.params;
    const { limit = 50, offset = 0 } = req.query;

    const job = await getJob(jobId);

    if (!job || job.userId !== req.userId) {
      return res.status(404).json({ error: 'Job not found' });
    }

    const posts = await getJobPosts(jobId, parseInt(limit as string), parseInt(offset as string));

    res.json({
      jobId,
      totalResults: job.resultCount,
      results: posts,
      limit: parseInt(limit as string),
      offset: parseInt(offset as string),
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch results' });
  }
});

router.get('/api/jobs', authenticateApiKey, checkRateLimitMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { limit = 50 } = req.query;

    const jobs = await getUserJobs(req.userId!, parseInt(limit as string));

    res.json(
      jobs.map((j) => ({
        id: j.id,
        platform: j.platform,
        jobType: j.jobType,
        query: j.query,
        status: j.status,
        progress: j.progress,
        resultCount: j.resultCount,
        createdAt: j.createdAt,
        completedAt: j.completedAt,
      }))
    );
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch jobs' });
  }
});

// ============ Webhook Routes ============
router.post('/api/webhooks', authenticateApiKey, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { url, events } = req.body;

    if (!url || !events || !Array.isArray(events)) {
      return res.status(400).json({ error: 'url and events array are required' });
    }

    const webhook = await createWebhook(req.userId!, url, events);

    res.json({
      id: webhook.id,
      secret: webhook.secret,
      createdAt: new Date(),
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to create webhook' });
  }
});

router.get('/api/webhooks', authenticateApiKey, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const webhooks = await getUserWebhooks(req.userId!);

    res.json(
      webhooks.map((w) => ({
        id: w.id,
        url: w.url,
        events: w.events,
        isActive: w.isActive,
        createdAt: w.createdAt,
      }))
    );
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch webhooks' });
  }
});

export default router;
