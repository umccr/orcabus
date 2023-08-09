import { Executor } from 'edgedb';
import e from '../../dbschema/edgeql-js';

export const resetDb = async (executor: Executor) => {
  await e.delete(e.audit.AuditEvent).run(executor);
  await e.delete(e.metadata.MetadataIdentifiable).run(executor);
};
