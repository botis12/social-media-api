import { chromium, Browser, Page, BrowserContext } from 'playwright';
import axios from 'axios';

const USER_AGENTS = [
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
];

const PROXIES = process.env.PROXY_LIST?.split(',').filter(Boolean) || [];
const TWO_CAPTCHA_API_KEY = process.env.TWO_CAPTCHA_API_KEY || '';

export interface ScrapedPost {
  id: string;
  platform: 'reddit' | 'twitter' | 'linkedin';
  author: string;
  title?: string;
  content: string;
  url?: string;
  likes: number;
  comments: number;
  shares: number;
  postedAt: Date;
  metadata?: Record<string, any>;
}

export interface ScrapedComment {
  id: string;
  postId: string;
  author: string;
  content: string;
  likes: number;
  postedAt: Date;
  metadata?: Record<string, any>;
}

// ─── 2Captcha solver ────────────────────────────────────────────────────────

async function solve2Captcha(siteKey: string, pageUrl: string): Promise<string | null> {
  if (!TWO_CAPTCHA_API_KEY) {
    console.warn('TWO_CAPTCHA_API_KEY not set — skipping CAPTCHA solve');
    return null;
  }

  try {
    const submitRes = await axios.post('https://2captcha.com/in.php', null, {
      params: {
        key: TWO_CAPTCHA_API_KEY,
        method: 'userrecaptcha',
        googlekey: siteKey,
        pageurl: pageUrl,
        json: 1,
      },
    });

    if (submitRes.data.status !== 1) {
      console.error('2Captcha submit failed:', submitRes.data);
      return null;
    }

    const taskId = submitRes.data.request;
    console.log('2Captcha task submitted:', taskId);

    for (let i = 0; i < 24; i++) {
      await new Promise((r) => setTimeout(r, 5000));
      const pollRes = await axios.get('https://2captcha.com/res.php', {
        params: { key: TWO_CAPTCHA_API_KEY, action: 'get', id: taskId, json: 1 },
      });

      if (pollRes.data.status === 1) {
        console.log('2Captcha solved');
        return pollRes.data.request;
      }
      if (pollRes.data.request !== 'CAPCHA_NOT_READY') {
        console.error('2Captcha error:', pollRes.data);
        return null;
      }
    }

    console.error('2Captcha timed out');
    return null;
  } catch (err) {
    console.error('2Captcha request failed:', err);
    return null;
  }
}

// ─── Base scraper ────────────────────────────────────────────────────────────

class BaseScraper {
  protected browser: Browser | null = null;
  protected context: BrowserContext | null = null;
  private pageCount = 0;
  private readonly MAX_PAGES = 10;

  protected getRandomUserAgent(): string {
    return USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)];
  }

  protected getRandomProxy(): string | undefined {
    if (PROXIES.length === 0) return undefined;
    return PROXIES[Math.floor(Math.random() * PROXIES.length)];
  }

  protected async initBrowser(): Promise<void> {
    await this.closeBrowser();

    const launchOptions: any = {
      headless: true,
      args: [
        '--disable-blink-features=AutomationControlled',
        '--disable-dev-shm-usage',
        '--no-first-run',
        '--no-default-browser-check',
        '--disable-extensions',
        '--disable-gpu',
      ],
    };

    const proxy = this.getRandomProxy();
    if (proxy) launchOptions.proxy = { server: proxy };

    this.browser = await chromium.launch(launchOptions);
    this.context = await this.browser.newContext({
      userAgent: this.getRandomUserAgent(),
      viewport: { width: 1920, height: 1080 },
      ignoreHTTPSErrors: true,
    });
    this.pageCount = 0;
  }

  // FIX: properly release all browser resources
  async closeBrowser(): Promise<void> {
    try { if (this.context) { await this.context.close(); this.context = null; } } catch (_) {}
    try { if (this.browser) { await this.browser.close(); this.browser = null; } } catch (_) {}
  }

  protected async createPage(): Promise<Page> {
    if (!this.browser || !this.context || this.pageCount >= this.MAX_PAGES) {
      await this.initBrowser();
    }

    this.pageCount++;
    const page = await this.context!.newPage();

    await page.addInitScript(() => {
      Object.defineProperty(navigator, 'webdriver', { get: () => false });
      Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
      Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
    });

    return page;
  }

  // FIX: real CAPTCHA solving via 2Captcha
  protected async handleCaptcha(page: Page): Promise<void> {
    const captchaFrames = await page.locator('iframe[src*="recaptcha"]').count();
    if (captchaFrames === 0) return;

    console.log('CAPTCHA detected, solving via 2Captcha...');

    const siteKey = await page.evaluate(() => {
      const el = document.querySelector('.g-recaptcha') as HTMLElement | null;
      return el?.getAttribute('data-sitekey') || null;
    });

    if (!siteKey) return;

    const token = await solve2Captcha(siteKey, page.url());
    if (!token) return;

    await page.evaluate((t: string) => {
      const el = document.getElementById('g-recaptcha-response') as HTMLTextAreaElement | null;
      if (el) el.value = t;
      const win = window as any;
      if (win.__recaptcha_cfg?.callback) win.__recaptcha_cfg.callback(t);
    }, token);

    await page.waitForTimeout(1000);
  }

  protected async retryWithBackoff<T>(
    fn: () => Promise<T>,
    maxRetries: number = 3,
    delay: number = 1000
  ): Promise<T> {
    for (let i = 0; i < maxRetries; i++) {
      try {
        return await fn();
      } catch (error) {
        if (i === maxRetries - 1) throw error;
        const waitTime = delay * Math.pow(2, i) + Math.random() * 1000;
        console.log(`Retry ${i + 1}/${maxRetries} in ${Math.round(waitTime)}ms`);
        await new Promise((resolve) => setTimeout(resolve, waitTime));
        await this.initBrowser();
      }
    }
    throw new Error('Max retries exceeded');
  }
}

// ─── Reddit scraper ──────────────────────────────────────────────────────────

export class RedditScraper extends BaseScraper {
  async getSubredditPosts(subreddit: string, limit: number = 25): Promise<ScrapedPost[]> {
    return this.retryWithBackoff(async () => {
      const page = await this.createPage();
      try {
        await page.goto(`https://www.reddit.com/r/${subreddit}/new/`, { waitUntil: 'networkidle', timeout: 30000 });
        await this.handleCaptcha(page);

        const posts: ScrapedPost[] = [];
        const postElements = await page.locator('[data-testid="post-container"]').all();

        for (let i = 0; i < Math.min(postElements.length, limit); i++) {
          const el = postElements[i];
          try {
            const title = await el.locator('[data-testid="post-title"]').textContent();
            const postLink = await el.locator('a[data-testid="internal-unauthenticated-comment-button"]').getAttribute('href');
            const author = await el.locator('[data-testid="post-author"]').textContent();
            const upvotes = await el.locator('[aria-label*="upvote"]').textContent();
            const comments = await el.locator('[aria-label*="comments"]').textContent();

            if (title && author) {
              posts.push({
                id: `reddit_${Date.now()}_${i}`,
                platform: 'reddit',
                author: author.trim(),
                title: title.trim(),
                content: title.trim(),
                url: postLink ? `https://reddit.com${postLink}` : undefined,
                likes: parseInt(upvotes?.match(/\d+/)?.[0] || '0'),
                comments: parseInt(comments?.match(/\d+/)?.[0] || '0'),
                shares: 0,
                postedAt: new Date(),
                metadata: { subreddit },
              });
            }
          } catch (e) {
            console.error(`Error parsing reddit post ${i}:`, e);
          }
        }

        return posts;
      } finally {
        await page.close();
      }
    });
  }
}

// ─── Twitter/X scraper ───────────────────────────────────────────────────────

export class TwitterScraper extends BaseScraper {
  async searchTweets(query: string, limit: number = 25): Promise<ScrapedPost[]> {
    return this.retryWithBackoff(async () => {
      const page = await this.createPage();
      try {
        await page.goto(`https://twitter.com/search?q=${encodeURIComponent(query)}&f=live`, { waitUntil: 'networkidle', timeout: 30000 });
        await this.handleCaptcha(page);
        await page.waitForSelector('[data-testid="tweet"]', { timeout: 15000 }).catch(() => {});

        const tweets: ScrapedPost[] = [];
        const tweetElements = await page.locator('[data-testid="tweet"]').all();

        for (let i = 0; i < Math.min(tweetElements.length, limit); i++) {
          const el = tweetElements[i];
          try {
            const content = await el.locator('[data-testid="tweetText"]').textContent().catch(() => null);
            const author = await el.locator('[data-testid="User-Name"]').textContent().catch(() => null);
            const likesLabel = await el.locator('[data-testid="like"]').getAttribute('aria-label').catch(() => null);
            const repliesLabel = await el.locator('[data-testid="reply"]').getAttribute('aria-label').catch(() => null);
            const retweetsLabel = await el.locator('[data-testid="retweet"]').getAttribute('aria-label').catch(() => null);
            const tweetLink = await el.locator('a[href*="/status/"]').first().getAttribute('href').catch(() => null);

            if (content && author) {
              tweets.push({
                id: `twitter_${Date.now()}_${i}`,
                platform: 'twitter',
                author: author.trim(),
                content: content.trim(),
                url: tweetLink ? `https://twitter.com${tweetLink}` : undefined,
                likes: parseInt(likesLabel?.match(/\d+/)?.[0] || '0'),
                comments: parseInt(repliesLabel?.match(/\d+/)?.[0] || '0'),
                shares: parseInt(retweetsLabel?.match(/\d+/)?.[0] || '0'),
                postedAt: new Date(),
                metadata: { query },
              });
            }
          } catch (e) {
            console.error(`Error parsing tweet ${i}:`, e);
          }
        }

        return tweets;
      } finally {
        await page.close();
      }
    });
  }
}

// ─── LinkedIn scraper (cookie-based auth) ───────────────────────────────────

export class LinkedInScraper extends BaseScraper {
  private sessionCookie: string | null = process.env.LINKEDIN_LI_AT_COOKIE || null;

  private async injectLinkedInSession(page: Page): Promise<void> {
    if (!this.sessionCookie) {
      throw new Error(
        'LinkedIn scraping requires LINKEDIN_LI_AT_COOKIE env variable. ' +
          'Log in to LinkedIn → DevTools → Application → Cookies → copy "li_at" value.'
      );
    }

    await page.context().addCookies([
      {
        name: 'li_at',
        value: this.sessionCookie,
        domain: '.linkedin.com',
        path: '/',
        httpOnly: true,
        secure: true,
      },
    ]);
  }

  async getCompanyPosts(companyName: string, limit: number = 25): Promise<ScrapedPost[]> {
    return this.retryWithBackoff(async () => {
      const page = await this.createPage();
      try {
        await this.injectLinkedInSession(page);

        const searchUrl = `https://www.linkedin.com/search/results/companies/?keywords=${encodeURIComponent(companyName)}`;
        await page.goto(searchUrl, { waitUntil: 'networkidle', timeout: 30000 });
        await this.handleCaptcha(page);

        // Navigate to company feed
        const companyUrl = await page.locator('.entity-result__title-text a').first().getAttribute('href').catch(() => null);
        if (companyUrl) {
          await page.goto(`https://www.linkedin.com${companyUrl.split('?')[0]}posts/`, { waitUntil: 'networkidle', timeout: 30000 });
          await this.handleCaptcha(page);
        }

        // Scroll to load posts
        for (let s = 0; s < 3; s++) {
          await page.evaluate(() => window.scrollBy(0, window.innerHeight));
          await page.waitForTimeout(1500);
        }

        const posts: ScrapedPost[] = [];
        const postElements = await page.locator('.feed-shared-update-v2').all();

        for (let i = 0; i < Math.min(postElements.length, limit); i++) {
          const el = postElements[i];
          try {
            const content = await el.locator('.feed-shared-update-v2__description').textContent().catch(() => null);
            const author = await el.locator('.update-components-actor__name').textContent().catch(() => null);
            const likesText = await el.locator('.social-details-social-counts__reactions-count').textContent().catch(() => null);
            const commentsText = await el.locator('.social-details-social-counts__comments').textContent().catch(() => null);

            if (content && author) {
              posts.push({
                id: `linkedin_${Date.now()}_${i}`,
                platform: 'linkedin',
                author: author.trim(),
                content: content.trim(),
                url: undefined,
                likes: parseInt(likesText?.replace(/[^0-9]/g, '') || '0'),
                comments: parseInt(commentsText?.match(/\d+/)?.[0] || '0'),
                shares: 0,
                postedAt: new Date(),
                metadata: { companyName },
              });
            }
          } catch (e) {
            console.error(`Error parsing LinkedIn post ${i}:`, e);
          }
        }

        return posts;
      } finally {
        await page.close();
      }
    });
  }
}

// ─── Singletons + graceful shutdown ─────────────────────────────────────────

export const redditScraper = new RedditScraper();
export const twitterScraper = new TwitterScraper();
export const linkedinScraper = new LinkedInScraper();

async function shutdown() {
  console.log('Closing all browser instances...');
  await Promise.allSettled([
    redditScraper.closeBrowser(),
    twitterScraper.closeBrowser(),
    linkedinScraper.closeBrowser(),
  ]);
  process.exit(0);
}

process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);
