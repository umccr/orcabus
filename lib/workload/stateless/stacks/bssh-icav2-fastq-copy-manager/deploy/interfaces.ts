import { ISecret } from 'aws-cdk-lib/aws-secretsmanager';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { IEventBus } from 'aws-cdk-lib/aws-events';
import { IStateMachine } from 'aws-cdk-lib/aws-stepfunctions';

export interface BsshIcav2FastqCopyManagerConfig {
  /* Required external properties */
  icav2TokenSecretId: string; // "ICAv2JWTKey-umccr-prod-service-trial"
  /* Event Bus Configurations */
  eventBusName: string; // OrcabusMain
  workflowName: string; // bsshFastqCopy
  workflowVersion: string; // 1.0.0
  serviceVersion: string; // 2024.05.15
  triggerLaunchSource: string; // orcabus.workflowmanager
  internalEventSource: string; // orcabus.bsshFastqCopy
  detailType: string; // WorkflowRunStateChange
}

export interface CreateManifestLambdaFunctionProps {
  icav2AccessToken: ISecret;
}

export interface EventBusProps {
  eventSource: string;
  detailType: string;
}

export interface CompletionEventProps extends EventBusProps {
  workflowName: string;
  workflowVersion: string;
  serviceVersion: string;
}

export interface BsshEventRuleProps extends EventBusProps {
  status: string;
  workflowName: string;
}

export interface Icav2EventBusProps {
  detailType: string;
}

export interface CreateBsshFastqCopyStateMachineProps {
  // Lambda function used to create the manifest
  manifestLambdaFunction: PythonFunction;
  // Event bus, to submit events to
  eventBus: IEventBus;
  // Event properties
  completionEventProps: CompletionEventProps;
  icav2CopyEventProps: Icav2EventBusProps;
  // Miscell
  sfnPrefix: string;
}

export interface BsshFastqCopyEventRuleProps {
  eventBusObj: IEventBus;
  eventBusProps: BsshEventRuleProps;
  stateMachine: IStateMachine;
}
