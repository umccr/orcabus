// must be first and before any DI is used
import 'reflect-metadata';
import { App } from '../app';
import { createDependencyContainer } from '../bootstrap/dependency-injection';
// import getAppSettings from '../bootstrap/settings';
import awsLambdaFastify, { PromiseHandler } from '@fastify/aws-lambda';

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export const handler = async (event: any, context: any) => {
  // const appSettings = getAppSettings();
  console.log('the event is:', event);

  const dc = await createDependencyContainer();
  const app = new App(dc);

  // Setting/registering server routes
  const server = await app.setupServer(dc);

  const proxy = awsLambdaFastify(server);
  return proxy(event, context);
};
