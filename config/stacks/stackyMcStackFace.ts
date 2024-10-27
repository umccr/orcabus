import {
  stackyPrimaryOutputUriSsmParameterName,
  stackyAnalysisCacheUriSsmParameterName,
  stackyAnalysisLogsUriSsmParameterName,
  stackyAnalysisOutputUriSsmParameterName,
  stackyEventBusName,
  stackyIcav2ProjectIdSsmParameterName,
  stackyInputMakerTableName,
  stackyInstrumentRunTableName,
  stackyWorkflowManagerTableName,
  stackyCttsov2InputGlueTableName,
  icav2AccessTokenSecretName,
  stackyWgtsQcGlueTableName,
  AppStage,
  stackyTnGlueTableName,
  stackyWtsGlueTableName,
  stackyUmccriseGlueTableName,
  stackyRnasumGlueTableName,
  stackyPierianDxGlueTableName,
  pieriandxProjectInfoSsmParameterPath,
  redcapLambdaFunctionName,
  stackyOncoanalyserGlueTableName,
  stackyOncoanalyserBothSashGlueTableName,
} from '../constants';
import { GlueStackConfig } from '../../lib/workload/stateless/stacks/stacky-mcstackface/glue-constructs';
import { StackyStatefulTablesConfig } from '../../lib/workload/stateful/stacks/stacky-mcstackface-dynamodb';

export const getGlueStackProps = (stage: AppStage): GlueStackConfig => {
  return {
    /* Events */
    eventBusName: stackyEventBusName,

    /* Tables */
    inputMakerTableName: stackyInputMakerTableName,
    instrumentRunTableName: stackyInstrumentRunTableName,
    workflowManagerTableName: stackyWorkflowManagerTableName,
    cttsov2GlueTableName: stackyCttsov2InputGlueTableName,
    wgtsQcGlueTableName: stackyWgtsQcGlueTableName,
    tnGlueTableName: stackyTnGlueTableName,
    wtsGlueTableName: stackyWtsGlueTableName,
    umccriseGlueTableName: stackyUmccriseGlueTableName,
    rnasumGlueTableName: stackyRnasumGlueTableName,
    pieriandxGlueTableName: stackyPierianDxGlueTableName,
    oncoanalyserGlueTableName: stackyOncoanalyserGlueTableName,
    oncoanalyserBothSashGlueTableName: stackyOncoanalyserBothSashGlueTableName,

    /* SSM Parameters */
    analysisCacheUriSsmParameterName: stackyAnalysisCacheUriSsmParameterName,
    analysisOutputUriSsmParameterName: stackyAnalysisOutputUriSsmParameterName,
    icav2ProjectIdSsmParameterName: stackyIcav2ProjectIdSsmParameterName,
    analysisLogsUriSsmParameterName: stackyAnalysisLogsUriSsmParameterName,

    /* Secrets */
    icav2AccessTokenSecretName: icav2AccessTokenSecretName[stage],

    /* BSSH SSM Parameters */
    bsshOutputFastqCopyUriSsmParameterName: stackyPrimaryOutputUriSsmParameterName,

    /* PierianDx SSM Parameters */
    pieriandxProjectInfoSsmParameterPath: pieriandxProjectInfoSsmParameterPath,
    redcapLambdaFunctionName: redcapLambdaFunctionName[stage],
  };
};

export const getStatefulGlueStackProps = (): StackyStatefulTablesConfig => {
  return {
    dynamodbInstrumentRunManagerTableName: stackyInstrumentRunTableName,
    dynamodbWorkflowManagerTableName: stackyWorkflowManagerTableName,
    dynamodbInputGlueTableName: stackyInputMakerTableName,
    dynamodbCttsov2WorkflowGlueTableName: stackyCttsov2InputGlueTableName,
    dynamodbWgtsQcGlueTableName: stackyWgtsQcGlueTableName,
    dynamodbTnGlueTableName: stackyTnGlueTableName,
    dynamodbWtsGlueTableName: stackyWtsGlueTableName,
    dynamodbUmccriseGlueTableName: stackyUmccriseGlueTableName,
    dynamodbRnasumGlueTableName: stackyRnasumGlueTableName,
    dynamodbPieriandxGlueTableName: stackyPierianDxGlueTableName,
    dynamodbOncoanalyserGlueTableName: stackyOncoanalyserGlueTableName,
    dynamodbOncoanalyserBothSashGlueTableName: stackyOncoanalyserBothSashGlueTableName,
  };
};
