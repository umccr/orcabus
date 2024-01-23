// must be first and before any DI is used
import 'reflect-metadata';
import { createDependencyContainer } from '../bootstrap/dependency-injection';
import insertScenario1 from './scenarios/scenario-1';
import insertScenario2 from './scenarios/scenario-2';

(async () => {
  if (!process.argv || process.argv.length <= 2) {
    throw new Error('Invalid argument');
  }

  const arg = process.argv.slice(2).join(' ');

  const dc = await createDependencyContainer();

  switch (arg) {
    case 'insert-scenario-1':
      await insertScenario1(dc);
      break;
    case 'insert-scenario-2':
      await insertScenario2(dc);
      break;

    default:
      throw new Error('Invalid argument');
  }
})();
