// **CDK and Constructs Imports**
import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';

// **AWS Services Imports**
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as events from 'aws-cdk-lib/aws-events';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import { Duration } from 'aws-cdk-lib';
import { DefinitionBody } from 'aws-cdk-lib/aws-stepfunctions';

// **Path and Custom Components Imports**
import path from 'path';
import { PythonLambdaLayerConstruct } from '../../../../components/python-lambda-layer';
import { PythonUvFunction } from '../../../../components/uv-python-lambda-image-builder';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';

// **Interfaces and Constants Imports**
import {
  BsshFastqCopyEventRuleProps,
  BsshIcav2FastqCopyManagerConfig,
  CreateBsshFastqCopyStateMachineProps,
  CreateManifestLambdaFunctionProps,
} from './interfaces';
import { icav2DataCopySyncDetailType } from '../../../../../../config/constants';

export type BsshIcav2FastqCopyManagerStackProps = BsshIcav2FastqCopyManagerConfig & cdk.StackProps;

export class BsshIcav2FastqCopyManagerStack extends cdk.Stack {
  public readonly bsshIcav2SfnMap = {
    prefix: 'bsshFastqCopy',
  };
  public readonly bsshIcav2FastqCopyEventMap = {
    triggerSource: 'orcabus.workflowmanager',
    triggerDetailType: 'WorkflowRunStateChange',
    triggerDetailStatus: 'READY',
  };

  constructor(scope: Construct, id: string, props: BsshIcav2FastqCopyManagerStackProps) {
    super(scope, id, props);

    // Get the icav2 jwt secret from lookup
    const icav2AccessToken = secretsmanager.Secret.fromSecretNameV2(
      this,
      'icav2_jwt_secret',
      props.icav2TokenSecretId
    );

    // Get eventbus object
    const eventBusObject = events.EventBus.fromEventBusName(this, 'event_bus', props.eventBusName);

    const bclconvertSuccessEventLambdaFunction = this.createManifestLambdaFunction({
      icav2AccessToken: icav2AccessToken,
    });

    const bsshCopyStateMachine = this.createBsshFastqCopyStateMachine({
      completionEventProps: {
        eventSource: props.internalEventSource,
        detailType: props.detailType,
        workflowName: props.workflowName,
        workflowVersion: props.workflowVersion,
        serviceVersion: props.serviceVersion,
      },
      eventBus: eventBusObject,
      icav2CopyEventProps: {
        detailType: icav2DataCopySyncDetailType,
      },
      manifestLambdaFunction: bclconvertSuccessEventLambdaFunction,
      sfnPrefix: this.bsshIcav2SfnMap.prefix,
    });

    // Add event rule to trigger the state machine
    this.addEventRuleToTriggerStateMachine({
      eventBusObj: eventBusObject,
      stateMachine: bsshCopyStateMachine,
      eventBusProps: {
        status: this.bsshIcav2FastqCopyEventMap.triggerDetailStatus,
        workflowName: props.workflowName,
        eventSource: this.bsshIcav2FastqCopyEventMap.triggerSource,
        detailType: this.bsshIcav2FastqCopyEventMap.triggerDetailType,
      },
    });
  }

  private createManifestLambdaFunction(props: CreateManifestLambdaFunctionProps): PythonFunction {
    // Get the lambda layer object
    const lambdaLayerObject = new PythonLambdaLayerConstruct(
      this,
      'icav2_fastq_copy_lambda_layer',
      {
        layerName: 'ICAv2FastqCopyManagerLayer',
        layerDescription: 'layer to enable the fastq copy manager tools layer',
        layerDirectory: path.join(__dirname, '../layers'),
      }
    ).lambdaLayerVersionObj;

    const bclconvertSuccessEventHandler = new PythonUvFunction(
      this,
      'bclconvert_success_event_lambda_python_function',
      {
        entry: path.join(__dirname, '../lambdas', 'query_bclconvert_outputs_handler_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'query_bclconvert_outputs_handler.py',
        handler: 'handler',
        timeout: Duration.seconds(900),
        memorySize: 2048,
        environment: {
          ICAV2_BASE_URL: 'https://ica.illumina.com/ica/rest',
          ICAV2_ACCESS_TOKEN_SECRET_ID: props.icav2AccessToken.secretName,
        },
        layers: [lambdaLayerObject],
      }
    );

    // Add permissions to the lambda function
    props.icav2AccessToken.grantRead(bclconvertSuccessEventHandler.currentVersion);

    // Return success event handler
    return bclconvertSuccessEventHandler;
  }

  private createBsshFastqCopyStateMachine(
    props: CreateBsshFastqCopyStateMachineProps
  ): sfn.IStateMachine {
    // Specify the statemachine and replace the arn placeholders with the lambda arns defined above
    const bsshFastqCopyStateMachine = new sfn.StateMachine(this, 'bssh_fastq_copy_state_machine', {
      stateMachineName: `${props.sfnPrefix}-run-icav2-fastq-copy`,
      // defintiontemplate
      definitionBody: DefinitionBody.fromFile(
        path.join(
          __dirname,
          '../step_functions_templates/bclconvert_success_event_state_machine.json'
        )
      ),
      // definitionSubstitutions
      definitionSubstitutions: {
        __bclconvert_success_event_lambda_arn__:
          props.manifestLambdaFunction.currentVersion.functionArn,
        __eventbus_name__: props.eventBus.eventBusName,
        __icav2_copy_detail_type__: props.icav2CopyEventProps.detailType,
        __detail_type__: props.completionEventProps.detailType,
        __event_source__: props.completionEventProps.eventSource,
        __workflow_name__: props.completionEventProps.workflowName,
        __workflow_version__: props.completionEventProps.workflowVersion,
        __payload_version__: props.completionEventProps.serviceVersion,
      },
    });

    // Allow the state machine to publish to the event bus
    props.eventBus.grantPutEventsTo(bsshFastqCopyStateMachine);

    // Allow the state machine to invoke the lambda function
    props.manifestLambdaFunction.currentVersion.grantInvoke(bsshFastqCopyStateMachine);

    return bsshFastqCopyStateMachine;
  }

  private addEventRuleToTriggerStateMachine(props: BsshFastqCopyEventRuleProps) {
    // Trigger state machine on event
    const rule = new events.Rule(this, 'bssh_fastq_copy_trigger_rule', {
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [props.eventBusProps.eventSource],
        detailType: [props.eventBusProps.detailType],
        detail: {
          status: [{ 'equals-ignore-case': props.eventBusProps.status }],
          workflowName: [{ 'equals-ignore-case': props.eventBusProps.workflowName }],
        },
      },
    });

    // Add rule
    rule.addTarget(
      new eventsTargets.SfnStateMachine(props.stateMachine, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );
  }
}
