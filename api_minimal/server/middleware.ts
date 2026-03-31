import { Request, Response, NextFunction } from 'express';
import { getApiKey, getUserCredits } from './db-helpers';
import { checkRateLimit } from './redis-utils';
import crypto from 'crypto';

export interface AuthenticatedRequest extends Request {
  apiKeyId?: number;
  userId?: number;
  apiKey?: string;
}

export async function authenticateApiKey(req: AuthenticatedRequest, res: Response, next: NextFunction) {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Missing or invalid Authorization header' });
  }

  const key = authHeader.substring(7);

  try {
    const apiKey = await getApiKey(key);

    if (!apiKey) {
      return res.status(401).json({ error: 'Invalid API key' });
    }

    if (!apiKey.isActive) {
      return res.status(401).json({ error: 'API key is inactive' });
    }

    req.apiKeyId = apiKey.id;
    req.userId = apiKey.userId;
    req.apiKey = key;

    next();
  } catch (error) {
    res.status(500).json({ error: 'Authentication error' });
  }
}

export async function checkRateLimitMiddleware(req: AuthenticatedRequest, res: Response, next: NextFunction) {
  if (!req.apiKeyId) {
    return res.status(401).json({ error: 'Unauthenticated' });
  }

  try {
    const apiKey = await getApiKey(req.apiKey!);
    if (!apiKey) {
      return res.status(401).json({ error: 'Invalid API key' });
    }

    const allowed = await checkRateLimit(req.apiKeyId, apiKey.rateLimit);

    if (!allowed) {
      return res.status(429).json({ error: 'Rate limit exceeded' });
    }

    next();
  } catch (error) {
    res.status(500).json({ error: 'Rate limit check failed' });
  }
}

export function checkCreditsMiddleware(creditsCost: number) {
  return async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
    if (!req.userId) {
      return res.status(401).json({ error: 'Unauthenticated' });
    }

    try {
      const credits = await getUserCredits(req.userId);

      if (!credits) {
        return res.status(402).json({ error: 'No credits available' });
      }

      const balance = parseFloat(credits.balance);
      if (balance < creditsCost) {
        return res.status(402).json({
          error: 'Insufficient credits',
          required: creditsCost,
          available: balance,
        });
      }

      next();
    } catch (error) {
      res.status(500).json({ error: 'Credit check failed' });
    }
  };
}

export function validateWebhookSignature(secret: string) {
  return (req: Request, res: Response, next: NextFunction) => {
    const signature = req.headers['x-webhook-signature'] as string;

    if (!signature) {
      return res.status(401).json({ error: 'Missing webhook signature' });
    }

    const payload = JSON.stringify(req.body);
    const hash = crypto.createHmac('sha256', secret).update(payload).digest('hex');

    if (hash !== signature) {
      return res.status(401).json({ error: 'Invalid webhook signature' });
    }

    next();
  };
}

export function errorHandler(err: any, req: Request, res: Response, next: NextFunction) {
  console.error('Error:', err);

  if (err.name === 'ValidationError') {
    return res.status(400).json({ error: err.message });
  }

  if (err.name === 'UnauthorizedError') {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  res.status(500).json({ error: 'Internal server error' });
}
