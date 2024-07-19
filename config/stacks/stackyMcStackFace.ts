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
  icav2AccessTokenSecretName,
  mockWgtsQcGlueTableName,
  AppStage,
} from '../constants';
import { GlueStackConfig } from '../../lib/workload/stateless/stacks/stacky-mcstackface/glue-constructs';
import { StackyStatefulTablesConfig } from '../../lib/workload/stateful/stacks/stacky-mcstackface-dynamodb';

export const getGlueStackProps = (stage: AppStage): GlueStackConfig => {
  return {
    /* SSM Parameters */
    bsshOutputFastqCopyUriSsmParameterName: mockPrimaryOutputUriSsmParameterName,
    analysisCacheUriSsmParameterName: mockAnalysisCacheUriSsmParameterName,
    analysisOutputUriSsmParameterName: mockAnalysisOutputUriSsmParameterName,
    icav2ProjectIdSsmParameterName: mockIcav2ProjectIdSsmParameterName,
    analysisLogsUriSsmParameterName: mockAnalysisLogsUriSsmParameterName,
    /* Events */
    eventBusName: mockEventBusName,
    /* Tables */
    inputMakerTableName: mockInputMakerTableName,
    instrumentRunTableName: mockInstrumentRunTableName,
    workflowManagerTableName: mockWorkflowManagerTableName,
    cttsov2GlueTableName: mockCttsov2InputGlueTableName,
    wgtsQcGlueTableName: mockWgtsQcGlueTableName,
    /* Secrets */
    icav2AccessTokenSecretName: icav2AccessTokenSecretName[stage],
  };
};

export const getStatefulGlueStackProps = (): StackyStatefulTablesConfig => {
  return {
    dynamodbInstrumentRunManagerTableName: mockInstrumentRunTableName,
    dynamodbWorkflowManagerTableName: mockWorkflowManagerTableName,
    dynamodbInputGlueTableName: mockInputMakerTableName,
    dynamodbCttsov2WorkflowGlueTableName: mockCttsov2InputGlueTableName,
    dynamodbWgtsQcGlueTableName: mockWgtsQcGlueTableName,
  };
};
