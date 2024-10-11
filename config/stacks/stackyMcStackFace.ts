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
  mockTnGlueTableName,
  mockWtsGlueTableName,
  mockUmccriseGlueTableName,
  mockRnasumGlueTableName,
  mockPierianDxGlueTableName,
  pieriandxProjectInfoSsmParameterPath,
  redcapLambdaFunctionName,
} from '../constants';
import { GlueStackConfig } from '../../lib/workload/stateless/stacks/stacky-mcstackface/glue-constructs';
import { StackyStatefulTablesConfig } from '../../lib/workload/stateful/stacks/stacky-mcstackface-dynamodb';

export const getGlueStackProps = (stage: AppStage): GlueStackConfig => {
  return {
    /* Events */
    eventBusName: mockEventBusName,

    /* Tables */
    inputMakerTableName: mockInputMakerTableName,
    instrumentRunTableName: mockInstrumentRunTableName,
    workflowManagerTableName: mockWorkflowManagerTableName,
    cttsov2GlueTableName: mockCttsov2InputGlueTableName,
    wgtsQcGlueTableName: mockWgtsQcGlueTableName,
    tnGlueTableName: mockTnGlueTableName,
    wtsGlueTableName: mockWtsGlueTableName,
    umccriseGlueTableName: mockUmccriseGlueTableName,
    rnasumGlueTableName: mockRnasumGlueTableName,
    pieriandxGlueTableName: mockPierianDxGlueTableName,

    /* SSM Parameters */
    analysisCacheUriSsmParameterName: mockAnalysisCacheUriSsmParameterName,
    analysisOutputUriSsmParameterName: mockAnalysisOutputUriSsmParameterName,
    icav2ProjectIdSsmParameterName: mockIcav2ProjectIdSsmParameterName,
    analysisLogsUriSsmParameterName: mockAnalysisLogsUriSsmParameterName,

    /* Secrets */
    icav2AccessTokenSecretName: icav2AccessTokenSecretName[stage],

    /* BSSH SSM Parameters */
    bsshOutputFastqCopyUriSsmParameterName: mockPrimaryOutputUriSsmParameterName,

    /* PierianDx SSM Parameters */
    pieriandxProjectInfoSsmParameterPath: pieriandxProjectInfoSsmParameterPath,
    redcapLambdaFunctionName: redcapLambdaFunctionName[stage],
  };
};

export const getStatefulGlueStackProps = (): StackyStatefulTablesConfig => {
  return {
    dynamodbInstrumentRunManagerTableName: mockInstrumentRunTableName,
    dynamodbWorkflowManagerTableName: mockWorkflowManagerTableName,
    dynamodbInputGlueTableName: mockInputMakerTableName,
    dynamodbCttsov2WorkflowGlueTableName: mockCttsov2InputGlueTableName,
    dynamodbWgtsQcGlueTableName: mockWgtsQcGlueTableName,
    dynamodbTnGlueTableName: mockTnGlueTableName,
    dynamodbWtsGlueTableName: mockWtsGlueTableName,
    dynamodbUmccriseGlueTableName: mockUmccriseGlueTableName,
    dynamodbRnasumGlueTableName: mockRnasumGlueTableName,
    dynamodbPieriandxGlueTableName: mockPierianDxGlueTableName,
  };
};
