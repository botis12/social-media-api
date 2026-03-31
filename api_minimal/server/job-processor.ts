import Queue from 'bull';
import { redditScraper, twitterScraper, linkedinScraper, ScrapedPost } from './scrapers';
import {
  updateJobStatus,
  savePosts,
  getJob,
  deductCredits,
  triggerWebhook,
  getUserWebhooks,
} from './db-helpers';
import { nanoid } from 'nanoid';

const jobQueue = new Queue('scraping-jobs', {
  redis: {
    host: process.env.REDIS_HOST || 'localhost',
    port: parseInt(process.env.REDIS_PORT || '6379'),
    password: process.env.REDIS_PASSWORD,
  },
});

export async function addScrapeJob(
  jobId: string,
  platform: 'reddit' | 'twitter' | 'linkedin',
  jobType: 'posts' | 'search' | 'company_posts',
  query: string,
  userId: number,
  limit: number = 25
): Promise<void> {
  await jobQueue.add(
    {
      jobId,
      platform,
      jobType,
      query,
      userId,
      limit,
    },
    {
      attempts: 3,
      backoff: {
        type: 'exponential',
        delay: 2000,
      },
      removeOnComplete: true,
      removeOnFail: false,
    }
  );
}

jobQueue.process(async (job) => {
  const { jobId, platform, jobType, query, userId, limit } = job.data;

  try {
    await updateJobStatus(jobId, 'processing', 0);

    let scrapedPosts: ScrapedPost[] = [];

    // Execute scraping based on platform
    if (platform === 'reddit' && jobType === 'posts') {
      scrapedPosts = await redditScraper.getSubredditPosts(query, limit);
    } else if (platform === 'twitter' && jobType === 'search') {
      scrapedPosts = await twitterScraper.searchTweets(query, limit);
    } else if (platform === 'linkedin' && jobType === 'company_posts') {
      scrapedPosts = await linkedinScraper.getCompanyPosts(query, limit);
    }

    // Save posts to database
    const postsToSave = scrapedPosts.map((post) => ({
      id: post.id,
      jobId,
      platform: post.platform,
      platformId: post.id,
      author: post.author,
      title: post.title || null,
      content: post.content,
      url: post.url || null,
      likes: post.likes,
      comments: post.comments,
      shares: post.shares,
      metadata: post.metadata ? JSON.stringify(post.metadata) : null,
      postedAt: post.postedAt,
    }));

    await savePosts(postsToSave);

    // Update job status
    await updateJobStatus(jobId, 'completed', 100, scrapedPosts.length);

    // Trigger webhooks
    const dbJob = await getJob(jobId);
    if (dbJob) {
      const webhooks = await getUserWebhooks(userId);
      for (const webhook of webhooks) {
        const events = Array.isArray(webhook.events) ? webhook.events : JSON.parse(webhook.events);
        if (events.includes('job.completed')) {
          await triggerWebhook(webhook.id, jobId, 'job.completed', {
            jobId,
            platform,
            resultCount: scrapedPosts.length,
            completedAt: new Date(),
          });
        }
      }
    }

    return { success: true, resultCount: scrapedPosts.length };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);

    // Update job status to failed
    await updateJobStatus(jobId, 'failed', 0, 0, errorMessage);

    // Trigger failure webhooks
    const dbJob = await getJob(jobId);
    if (dbJob) {
      const webhooks = await getUserWebhooks(userId);
      for (const webhook of webhooks) {
        const events = Array.isArray(webhook.events) ? webhook.events : JSON.parse(webhook.events);
        if (events.includes('job.failed')) {
          await triggerWebhook(webhook.id, jobId, 'job.failed', {
            jobId,
            platform,
            error: errorMessage,
            failedAt: new Date(),
          });
        }
      }
    }

    throw error;
  }
});

jobQueue.on('completed', (job) => {
  console.log(`Job ${job.id} completed:`, job.returnvalue);
});

jobQueue.on('failed', (job, err) => {
  console.error(`Job ${job.id} failed:`, err.message);
});

export async function getQueueStats(): Promise<any> {
  const counts = await jobQueue.getJobCounts();
  return {
    active: counts.active,
    completed: counts.completed,
    failed: counts.failed,
    delayed: counts.delayed,
    waiting: counts.waiting,
  };
}

export async function closeJobQueue(): Promise<void> {
  await jobQueue.close();
}

export default jobQueue;
