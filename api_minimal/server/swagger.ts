import swaggerJsdoc from 'swagger-jsdoc';

const options = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'Social Media Data Extraction API',
      version: '1.0.0',
      description: 'A production-ready API for extracting structured data from Reddit, Twitter, and LinkedIn with anti-bot bypass mechanisms.',
      contact: {
        name: 'API Support',
        url: 'https://example.com/support',
      },
    },
    servers: [
      {
        url: process.env.API_URL || 'http://localhost:3000',
        description: 'API Server',
      },
    ],
    components: {
      securitySchemes: {
        bearerAuth: {
          type: 'http',
          scheme: 'bearer',
          bearerFormat: 'JWT',
          description: 'Bearer token authentication using API key',
        },
      },
      schemas: {
        ApiKey: {
          type: 'object',
          properties: {
            id: { type: 'integer' },
            key: { type: 'string', description: 'API key (starts with sk_)' },
            name: { type: 'string' },
            rateLimit: { type: 'integer', default: 100 },
            isActive: { type: 'boolean' },
            lastUsedAt: { type: 'string', format: 'date-time' },
            createdAt: { type: 'string', format: 'date-time' },
          },
        },
        Credits: {
          type: 'object',
          properties: {
            balance: { type: 'string', description: 'Current credit balance' },
            totalUsed: { type: 'string', description: 'Total credits used' },
            updatedAt: { type: 'string', format: 'date-time' },
          },
        },
        Job: {
          type: 'object',
          properties: {
            id: { type: 'string' },
            platform: { type: 'string', enum: ['reddit', 'twitter', 'linkedin'] },
            jobType: { type: 'string', enum: ['posts', 'search', 'company_posts'] },
            query: { type: 'string' },
            status: { type: 'string', enum: ['pending', 'processing', 'completed', 'failed'] },
            progress: { type: 'integer', minimum: 0, maximum: 100 },
            resultCount: { type: 'integer' },
            error: { type: 'string', nullable: true },
            createdAt: { type: 'string', format: 'date-time' },
            completedAt: { type: 'string', format: 'date-time', nullable: true },
          },
        },
        Post: {
          type: 'object',
          properties: {
            id: { type: 'string' },
            platform: { type: 'string', enum: ['reddit', 'twitter', 'linkedin'] },
            author: { type: 'string' },
            title: { type: 'string', nullable: true },
            content: { type: 'string' },
            url: { type: 'string', nullable: true },
            likes: { type: 'integer' },
            comments: { type: 'integer' },
            shares: { type: 'integer' },
            postedAt: { type: 'string', format: 'date-time' },
          },
        },
        Webhook: {
          type: 'object',
          properties: {
            id: { type: 'integer' },
            url: { type: 'string', format: 'uri' },
            events: { type: 'array', items: { type: 'string' } },
            isActive: { type: 'boolean' },
            createdAt: { type: 'string', format: 'date-time' },
          },
        },
        Error: {
          type: 'object',
          properties: {
            error: { type: 'string' },
          },
        },
      },
    },
    security: [
      {
        bearerAuth: [],
      },
    ],
  },
  apis: ['./server/api-routes.ts'],
};

export const swaggerSpec = swaggerJsdoc(options);
