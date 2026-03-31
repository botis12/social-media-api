import express from 'express';
import swaggerUi from 'swagger-ui-express';
import { swaggerSpec } from './swagger';
import apiRoutes from './api-routes';
import { errorHandler } from './middleware';
import { startWebhookProcessor } from './webhook-service';
import jobQueue, { getQueueStats } from './job-processor';

export function createCustomServer(app: express.Application): void {
  // Middleware
  app.use(express.json());
  app.use(express.urlencoded({ extended: true }));

  // CORS headers
  app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization');
    res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    if (req.method === 'OPTIONS') {
      return res.sendStatus(200);
    }
    next();
  });

  // Health check endpoint
  app.get('/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date() });
  });

  // API Documentation
  app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));

  // API Routes
  app.use(apiRoutes);

  // Stats endpoint
  app.get('/api/stats', async (req, res) => {
    try {
      const queueStats = await getQueueStats();
      res.json({
        queue: queueStats,
        timestamp: new Date(),
      });
    } catch (error) {
      res.status(500).json({ error: 'Failed to fetch stats' });
    }
  });

  // Error handling
  app.use(errorHandler);

  // 404 handler
  app.use((req, res) => {
    res.status(404).json({ error: 'Not found' });
  });

  // Start webhook processor
  startWebhookProcessor(30000);

  console.log('Custom server setup complete');
}
