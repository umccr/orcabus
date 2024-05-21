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
        schemaName: 'orcabus.sequencerunmanager@SequenceRunStateChange',
        schemaDescription: 'State change event for sequencing run by SequenceRunManager',
        schemaLocation: path.join(
          __dirname,
          docBase + '/sequencerunmanager/SequenceRunStateChange.json'
        ),
      },
      {
        ...defaultProps,
        schemaName: 'orcabus.workflowmanager@WorkflowRunStateChange',
        schemaDescription: 'State change event for workflow run by WorkflowManager',
        schemaLocation: path.join(
          __dirname,
          docBase + '/workflowmanager/WorkflowRunStateChange.json'
        ),
      },
      {
        ...defaultProps,
        schemaName: 'orcabus.bclconvertmanager@WorkflowRunStateChange',
        schemaDescription: 'State change event for workflow run by BclConvertManager',
        schemaLocation: path.join(
          __dirname,
          docBase + '/bclconvertmanager/WorkflowRunStateChange.json'
        ),
      },
    ],
  };
};
