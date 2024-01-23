// 'reflect-metadata' must be beginning of the line and before any DI is used
import 'reflect-metadata';
import { App } from '../app';
import { createDependencyContainer } from '../bootstrap/dependency-injection';
import awsLambdaFastify from '@fastify/aws-lambda';

export const handler = async (event: unknown, context: unknown) => {
  const dc = await createDependencyContainer();
  const app = new App(dc);

  // Setting/registering server routes
  const server = await app.setupServer();

  const proxy = awsLambdaFastify(server);
  return proxy(event, context);
};
