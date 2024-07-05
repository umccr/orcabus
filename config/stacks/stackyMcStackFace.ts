import {
  mockPrimaryOutputUriSsmParameterName,
  mockAnalysisCacheUriSsmParameterName,
  mockAnalysisLogsUriSsmParameterName,
  mockAnalysisOutputUriSsmParameterName,
  mockEventBusName,
  mockIcav2ProjectIdSsmParameterName,
  mockInputMakerTableName,
  mockInstrumentRunTableName,
  mockWorkflowManagerTableName,
  mockCttsov2InputGlueTableName,
} from '../constants';
import { GlueStackConfig } from '../../lib/workload/stateless/stacks/stacky-mcstackface/glue-constructs';
import { StackyStatefulTablesConfig } from '../../lib/workload/stateful/stacks/stacky-mcstackface-dynamodb';

export const getGlueStackProps = (): GlueStackConfig => {
  return {
    bsshOutputFastqCopyUriSsmParameterName: mockPrimaryOutputUriSsmParameterName,
    analysisCacheUriSsmParameterName: mockAnalysisCacheUriSsmParameterName,
    analysisOutputUriSsmParameterName: mockAnalysisOutputUriSsmParameterName,
    analysisLogsUriSsmParameterName: mockAnalysisLogsUriSsmParameterName,
    eventBusName: mockEventBusName,
    icav2ProjectIdSsmParameterName: mockIcav2ProjectIdSsmParameterName,
    inputMakerTableName: mockInputMakerTableName,
    instrumentRunTableName: mockInstrumentRunTableName,
    workflowManagerTableName: mockWorkflowManagerTableName,
    cttsov2GlueTableName: mockCttsov2InputGlueTableName,
  };
};

export const getStatefulGlueStackProps = (): StackyStatefulTablesConfig => {
  return {
    dynamodbInstrumentRunManagerTableName: mockInstrumentRunTableName,
    dynamodbWorkflowManagerTableName: mockWorkflowManagerTableName,
    dynamodbInputGlueTableName: mockInputMakerTableName,
    dynamodbCttsov2WorkflowGlueTableName: mockCttsov2InputGlueTableName,
  };
};
