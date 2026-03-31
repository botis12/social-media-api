import { int, mysqlEnum, mysqlTable, text, timestamp, varchar, bigint, decimal, json, boolean } from "drizzle-orm/mysql-core";
import { relations } from "drizzle-orm";

/**
 * Core user table backing auth flow.
 * Extend this file with additional tables as your product grows.
 * Columns use camelCase to match both database fields and generated types.
 */
export const users = mysqlTable("users", {
  /**
   * Surrogate primary key. Auto-incremented numeric value managed by the database.
   * Use this for relations between tables.
   */
  id: int("id").autoincrement().primaryKey(),
  /** Manus OAuth identifier (openId) returned from the OAuth callback. Unique per user. */
  openId: varchar("openId", { length: 64 }).notNull().unique(),
  name: text("name"),
  email: varchar("email", { length: 320 }),
  loginMethod: varchar("loginMethod", { length: 64 }),
  role: mysqlEnum("role", ["user", "admin"]).default("user").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  lastSignedIn: timestamp("lastSignedIn").defaultNow().notNull(),
});

export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;

// API Keys table
export const apiKeys = mysqlTable("api_keys", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  key: varchar("key", { length: 128 }).notNull().unique(),
  name: varchar("name", { length: 255 }).notNull(),
  isActive: boolean("isActive").default(true).notNull(),
  rateLimit: int("rateLimit").default(100).notNull(), // requests per minute
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  lastUsedAt: timestamp("lastUsedAt"),
});

export type ApiKey = typeof apiKeys.$inferSelect;
export type InsertApiKey = typeof apiKeys.$inferInsert;

// Usage Credits table
export const usageCredits = mysqlTable("usage_credits", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  balance: decimal("balance", { precision: 12, scale: 2 }).default("0").notNull(),
  totalUsed: decimal("totalUsed", { precision: 12, scale: 2 }).default("0").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type UsageCredit = typeof usageCredits.$inferSelect;
export type InsertUsageCredit = typeof usageCredits.$inferInsert;

// Scraping Jobs table
export const jobs = mysqlTable("jobs", {
  id: varchar("id", { length: 64 }).primaryKey(),
  userId: int("userId").notNull(),
  apiKeyId: int("apiKeyId").notNull(),
  platform: mysqlEnum("platform", ["reddit", "twitter", "linkedin"]).notNull(),
  jobType: mysqlEnum("jobType", ["posts", "search", "company_posts"]).notNull(),
  query: text("query").notNull(),
  status: mysqlEnum("status", ["pending", "processing", "completed", "failed"]).default("pending").notNull(),
  progress: int("progress").default(0).notNull(),
  resultCount: int("resultCount").default(0).notNull(),
  creditsCost: decimal("creditsCost", { precision: 10, scale: 2 }).default("0").notNull(),
  error: text("error"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  completedAt: timestamp("completedAt"),
});

export type Job = typeof jobs.$inferSelect;
export type InsertJob = typeof jobs.$inferInsert;

// Posts table
export const posts = mysqlTable("posts", {
  id: varchar("id", { length: 128 }).primaryKey(),
  jobId: varchar("jobId", { length: 64 }).notNull(),
  platform: mysqlEnum("platform", ["reddit", "twitter", "linkedin"]).notNull(),
  platformId: varchar("platformId", { length: 255 }).notNull(),
  author: varchar("author", { length: 255 }).notNull(),
  title: text("title"),
  content: text("content").notNull(),
  url: varchar("url", { length: 2048 }),
  likes: int("likes").default(0).notNull(),
  comments: int("comments").default(0).notNull(),
  shares: int("shares").default(0).notNull(),
  metadata: json("metadata"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  postedAt: timestamp("postedAt"),
});

export type Post = typeof posts.$inferSelect;
export type InsertPost = typeof posts.$inferInsert;

// Comments table
export const comments = mysqlTable("comments", {
  id: varchar("id", { length: 128 }).primaryKey(),
  postId: varchar("postId", { length: 128 }).notNull(),
  author: varchar("author", { length: 255 }).notNull(),
  content: text("content").notNull(),
  likes: int("likes").default(0).notNull(),
  metadata: json("metadata"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  postedAt: timestamp("postedAt"),
});

export type Comment = typeof comments.$inferSelect;
export type InsertComment = typeof comments.$inferInsert;

// Webhooks table
export const webhooks = mysqlTable("webhooks", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  url: varchar("url", { length: 2048 }).notNull(),
  events: json("events").notNull(), // ['job.completed', 'job.failed']
  isActive: boolean("isActive").default(true).notNull(),
  secret: varchar("secret", { length: 255 }).notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type Webhook = typeof webhooks.$inferSelect;
export type InsertWebhook = typeof webhooks.$inferInsert;

// Webhook Events Log table
export const webhookEvents = mysqlTable("webhook_events", {
  id: int("id").autoincrement().primaryKey(),
  webhookId: int("webhookId").notNull(),
  jobId: varchar("jobId", { length: 64 }),
  event: varchar("event", { length: 64 }).notNull(),
  payload: json("payload").notNull(),
  status: mysqlEnum("status", ["pending", "sent", "failed"]).default("pending").notNull(),
  attempts: int("attempts").default(0).notNull(),
  lastAttemptAt: timestamp("lastAttemptAt"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type WebhookEvent = typeof webhookEvents.$inferSelect;
export type InsertWebhookEvent = typeof webhookEvents.$inferInsert;