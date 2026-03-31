import axios from 'axios';
import crypto from 'crypto';
import { getPendingWebhookEvents, updateWebhookEventStatus } from './db-helpers';
import { getDb } from './db';
import { webhooks } from '../drizzle/schema';
import { eq } from 'drizzle-orm';

const MAX_RETRY_ATTEMPTS = 5;
const INITIAL_RETRY_DELAY = 5000; // 5 seconds

export async function deliverWebhookEvent(eventId: number, webhookId: number, payload: any, secret: string): Promise<boolean> {
  try {
    const db = await getDb();
    if (!db) return false;

    const webhook = await db.select().from(webhooks).where(eq(webhooks.id, webhookId)).limit(1);
    if (webhook.length === 0) return false;

    const webhookUrl = webhook[0].url;
    const payloadJson = JSON.stringify(payload);
    const signature = crypto.createHmac('sha256', secret).update(payloadJson).digest('hex');

    const response = await axios.post(webhookUrl, payload, {
      headers: {
        'Content-Type': 'application/json',
        'X-Webhook-Signature': signature,
        'X-Webhook-ID': `evt_${Date.now()}`,
      },
      timeout: 10000,
    });

    if (response.status >= 200 && response.status < 300) {
      await updateWebhookEventStatus(eventId, 'sent', 1);
      return true;
    } else {
      throw new Error(`Webhook returned status ${response.status}`);
    }
  } catch (error) {
    console.error(`Failed to deliver webhook event ${eventId}:`, error);
    return false;
  }
}

export async function processWebhookQueue(): Promise<void> {
  const pendingEvents = await getPendingWebhookEvents(10);

  for (const event of pendingEvents) {
    const db = await getDb();
    if (!db) continue;

    const webhook = await db.select().from(webhooks).where(eq(webhooks.id, event.webhookId)).limit(1);
    if (webhook.length === 0) continue;

    const maxRetries = MAX_RETRY_ATTEMPTS;
    const shouldRetry = event.attempts < maxRetries;

    const success = await deliverWebhookEvent(
      event.id,
      event.webhookId,
      event.payload,
      webhook[0].secret
    );

    if (!success && shouldRetry) {
      // Calculate exponential backoff delay
      const delay = INITIAL_RETRY_DELAY * Math.pow(2, event.attempts);
      console.log(`Webhook event ${event.id} will retry in ${delay}ms`);

      // Update attempts but keep status as pending
      await updateWebhookEventStatus(event.id, 'pending', event.attempts + 1);
    } else if (!success) {
      // Max retries exceeded, mark as failed
      await updateWebhookEventStatus(event.id, 'failed', maxRetries);
      console.error(`Webhook event ${event.id} failed after ${maxRetries} attempts`);
    }
  }
}

export function startWebhookProcessor(intervalMs: number = 30000): NodeJS.Timer {
  return setInterval(async () => {
    try {
      await processWebhookQueue();
    } catch (error) {
      console.error('Error processing webhook queue:', error);
    }
  }, intervalMs);
}
