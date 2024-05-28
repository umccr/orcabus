import {
  mockBclconvertInteropQcUriPrefixSsmParameterName,
  mockBsshOutputFastqCopyUriPrefixSsmParameterName,
  mockCttsov2CacheUriPrefixSsmParameterName,
  mockCttsov2OutputUriPrefixSsmParameterName,
  mockEventBusName,
  mockIcav2ProjectIdSsmParameterName,
  mockInputMakerTableName,
  mockInstrumentRunTableName,
  mockWorkflowManagerTableName,
} from '../constants';
import { GlueStackConfig } from '../../lib/workload/stateless/stacks/stacky-mcstackface/glue-constructs';
import {StackyStatefulTablesConfig} from "../../lib/workload/stateful/stacks/stacky-mcstackface-dynamodb";

export const getGlueStackProps = (): GlueStackConfig => {
  return {
    bclconvertInteropQcUriPrefixSsmParameterName: mockBclconvertInteropQcUriPrefixSsmParameterName,
    bsshOutputFastqCopyUriPrefixSsmParameterName: mockBsshOutputFastqCopyUriPrefixSsmParameterName,
    cttsov2CacheUriPrefixSsmParameterName: mockCttsov2CacheUriPrefixSsmParameterName,
    cttsov2OutputUriPrefixSsmParameterName: mockCttsov2OutputUriPrefixSsmParameterName,
    eventBusName: mockEventBusName,
    icav2ProjectIdSsmParameterName: mockIcav2ProjectIdSsmParameterName,
    inputMakerTableName: mockInstrumentRunTableName,
    instrumentRunTableName: mockInputMakerTableName,
    workflowManagerTableName: mockWorkflowManagerTableName,
  };
};

export const getStatefulGlueStackProps = (): StackyStatefulTablesConfig => {
  return {
    dynamodbInstrumentRunManagerTableName: mockInstrumentRunTableName,
    dynamodbWorkflowManagerTableName: mockWorkflowManagerTableName,
    dynamodbInputGlueTableName: mockInputMakerTableName,
  };
}
