import { SchemaStackProps } from '../../lib/workload/stateless/stacks/schema/stack';
import { schemaRegistryName } from '../constants';
import path from 'path';

export const getSchemaStackProps = (): SchemaStackProps => {
  const docBase: string = '../../docs/event-schemas';
  const defaultProps = {
    schemaType: 'OpenApi3',
  };

  return {
    registryName: schemaRegistryName,
    schemas: [
      // add your schema into this `schemas` array
      // adjust name, description, location accordingly
      {
        ...defaultProps,
        schemaName: 'orcabus.srm@SequenceRunStateChange',
        schemaDescription: 'State change event for sequencing run',
        schemaLocation: path.join(__dirname, docBase + '/srm/SequenceRunStateChange.json'),
      },
    ],
  };
};
