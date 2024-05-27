import { SchemaStackProps } from '../../../lib/workload/stateless/stacks/schema/stack';
import { eventSchemaRegistryName } from '../../constants';
import path from 'path';

export const getEventSchemaStackProps = (): SchemaStackProps => {
  const docBase: string = '../../../docs/schemas/events';
  const defaultProps = {
    schemaType: 'OpenApi3',
  };

  return {
    registryName: eventSchemaRegistryName,
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
        schemaName: 'orcabus.executionservice@WorkflowRunStateChange',
        schemaDescription: 'State change event for workflow run by workflow execution services',
        schemaLocation: path.join(
          __dirname,
          docBase + '/executionservice/WorkflowRunStateChange.json'
        ),
      },
    ],
  };
};
