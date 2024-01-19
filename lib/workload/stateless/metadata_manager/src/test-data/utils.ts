import { Client } from 'edgedb';
import e from '../../dbschema/edgeql-js';

export const blankDb = async (edgeDbClient: Client) => {
  await e.delete(e.metadata.Subject).run(edgeDbClient);
  await e.delete(e.metadata.Specimen).run(edgeDbClient);
  await e.delete(e.metadata.Library).run(edgeDbClient);
};
