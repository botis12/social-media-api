-- Add indexes for performance optimization

-- API Keys indexes
CREATE INDEX idx_api_keys_user_id ON api_keys(userId);
CREATE INDEX idx_api_keys_is_active ON api_keys(isActive);

-- Usage Credits indexes
CREATE INDEX idx_usage_credits_user_id ON usage_credits(userId);

-- Jobs indexes
CREATE INDEX idx_jobs_user_id ON jobs(userId);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_created_at ON jobs(createdAt);
CREATE INDEX idx_jobs_platform ON jobs(platform);

-- Posts indexes
CREATE INDEX idx_posts_job_id ON posts(jobId);
CREATE INDEX idx_posts_platform ON posts(platform);
CREATE INDEX idx_posts_author ON posts(author);
CREATE INDEX idx_posts_created_at ON posts(createdAt);

-- Comments indexes
CREATE INDEX idx_comments_post_id ON comments(postId);
CREATE INDEX idx_comments_author ON comments(author);
CREATE INDEX idx_comments_created_at ON comments(createdAt);

-- Webhooks indexes
CREATE INDEX idx_webhooks_user_id ON webhooks(userId);
CREATE INDEX idx_webhooks_is_active ON webhooks(isActive);

-- Webhook Events indexes
CREATE INDEX idx_webhook_events_webhook_id ON webhook_events(webhookId);
CREATE INDEX idx_webhook_events_status ON webhook_events(status);
CREATE INDEX idx_webhook_events_job_id ON webhook_events(jobId);
CREATE INDEX idx_webhook_events_created_at ON webhook_events(createdAt);
