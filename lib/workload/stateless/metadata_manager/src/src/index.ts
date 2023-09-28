// must be first and before any DI is used
import 'reflect-metadata';
import { App } from './app';
import { createDependencyContainer } from './bootstrap/dependency-injection';
import getAppSettings from './bootstrap/settings';

import awsLambdaFastify, { PromiseHandler } from '@fastify/aws-lambda';

// const init = require('./app');

// const proxy = awsLambdaFastify(init());
// // or
// const proxy = awsLambdaFastify(init(), { binaryMimeTypes: ['application/octet-stream'] })

export const handler = async (handler: PromiseHandler) => {
  const appSettings = getAppSettings();

  const dc = await createDependencyContainer();
  const app = new App(dc);

  // Setting/registering server routes
  const server = await app.setupServer(dc);

  // server.listen({ host: appSettings.host, port: appSettings.port }, (err, address) => {
  //   if (err) {
  //     console.error(err);
  //     process.exit(1);
  //   }
  //   console.log(`Server listening at ${address}`);
  // });

  return awsLambdaFastify(server);
};
