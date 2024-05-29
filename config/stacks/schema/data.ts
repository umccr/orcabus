import { SchemaStackProps } from '../../../lib/workload/stateless/stacks/schema/stack';
import { dataSchemaRegistryName } from '../../constants';
import path from 'path';

export const getDataSchemaStackProps = (): SchemaStackProps => {
  const docBase: string = '../../../docs/schemas/data';
  const defaultProps = {
    schemaType: 'JSONSchemaDraft4',
  };

  return {
    registryName: dataSchemaRegistryName,
    schemas: [
      // add your schema into this `schemas` array
      // adjust name, description, location accordingly
      {
        ...defaultProps,
        schemaName: 'orcabus.bclconvertmanager@PayloadDataSucceeded',
        schemaDescription: 'PayloadDataSucceeded data schema by bclconvertmanager',
        schemaLocation: path.join(
          __dirname,
          docBase + '/bclconvertmanager/PayloadDataSucceeded.schema.json'
        ),
      },
      {
        ...defaultProps,
        schemaName: 'orcabus.bsshicav2fastqcopymanager@PayloadDataReady',
        schemaDescription: 'PayloadDataReady data schema by bsshicav2fastqcopymanager',
        schemaLocation: path.join(
          __dirname,
          docBase + '/bsshicav2fastqcopymanager/PayloadDataReady.schema.json'
        ),
      },
      {
        ...defaultProps,
        schemaName: 'orcabus.bsshicav2fastqcopymanager@PayloadDataSucceeded',
        schemaDescription: 'PayloadDataSucceeded data schema by bsshicav2fastqcopymanager',
        schemaLocation: path.join(
          __dirname,
          docBase + '/bsshicav2fastqcopymanager/PayloadDataSucceeded.schema.json'
        ),
      },
    ],
  };
};
