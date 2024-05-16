import * as cdk from 'aws-cdk-lib';
import { Duration } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import * as events_targets from 'aws-cdk-lib/aws-events-targets';
import { DefinitionBody } from 'aws-cdk-lib/aws-stepfunctions';

import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';

interface BsshIcav2FastqCopyStateMachineConstructProps {
  /* Stack objects */
  icav2CopyBatchStateMachineObj: sfn.IStateMachine;
  icav2JwtSecretObj: secretsmanager.ISecret;
  lambdasLayerObj: lambda.ILayerVersion;
  eventBusObj: events.IEventBus; // Orcabus main event
  /* Lambda paths */
  bclconvertSuccessEventHandlerLambdaPath: string; // __dirname + '/../../../lambdas/bclconvert_success_event_handler'
  /* State machine */
  stateMachineName: string; // 'bssh-fastq-copy-sfn '
  workflowDefinitionBodyPath: string; // __dirname + '../step_functions_templates/bclconvert_success_event_state_machine.json'
  // Event handling //
  detailType: string; // workflowRunStateChange
  serviceVersion: string; // 2024.05.15
  triggerLaunchSource: string; // orcabus.wfm
  internalEventSource: string; // orcabus.bssh_fastq_copy
  workflowType: string; // bssh_fastq_copy
  workflowVersion: string; // 1.0.0
}

export class BsshIcav2FastqCopyStateMachineConstruct extends Construct {
  constructor(scope: Construct, id: string, props: BsshIcav2FastqCopyStateMachineConstructProps) {
    super(scope, id);

    // Handle bclconvert success lambda
    const bclconvert_success_event_lambda = new PythonFunction(
      this,
      'bclconvert_success_event_lambda_python_function',
      {
        entry: props.bclconvertSuccessEventHandlerLambdaPath,
        runtime: lambda.Runtime.PYTHON_3_11,
        architecture: lambda.Architecture.ARM_64,
        index: 'query_bclconvert_outputs_handler_lambda.py',
        handler: 'handler',
        memorySize: 1024,
        layers: [props.lambdasLayerObj],
        timeout: Duration.seconds(60),
        environment: {
          ICAV2_BASE_URL: 'https://ica.illumina.com/ica/rest',
          ICAV2_ACCESS_TOKEN_SECRET_ID: props.icav2JwtSecretObj.secretName,
        },
      }
    );

    // Add icav2 secrets permissions to lambda
    props.icav2JwtSecretObj.grantRead(
      <iam.IRole>bclconvert_success_event_lambda.currentVersion.role
    );

    // Specify the statemachine and replace the arn placeholders with the lambda arns defined above
    const stateMachine = new sfn.StateMachine(this, 'bssh_fastq_copy_state_machine', {
      // State machine name
      stateMachineName: props.stateMachineName,
      // defintiontemplate
      definitionBody: DefinitionBody.fromFile(props.workflowDefinitionBodyPath),
      // definitionSubstitutions
      definitionSubstitutions: {
        __bclconvert_success_event_lambda_arn__:
          bclconvert_success_event_lambda.currentVersion.functionArn,
        __copy_batch_data_state_machine_arn__: props.icav2CopyBatchStateMachineObj.stateMachineArn,
        __eventbus_name__: props.eventBusObj.eventBusName,
        __detail_type__: props.detailType,
        __event_source__: props.internalEventSource,
      },
    });

    // Add lambda invoke permissions to stateMachine role
    bclconvert_success_event_lambda.currentVersion.grantInvoke(stateMachine.role);

    // Allow the icav2 copy batch statemachine to be started by the bssh fastq copy manager

    // Because we run a nested state machine, we need to add the permissions to the state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    stateMachine.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );

    // State machine
    props.icav2CopyBatchStateMachineObj.grantStartExecution(stateMachine.role);

    // Trigger state machine on event
    const rule = new events.Rule(this, 'bssh_fastq_copy_trigger_rule', {
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [props.triggerLaunchSource],
        detailType: [props.detailType],
        detail: {
          status: ['ready'],
        },
      },
    });

    // Add rule
    rule.addTarget(
      new events_targets.SfnStateMachine(stateMachine, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );

    // Allow the statemachine to submit events to the event bus
    props.eventBusObj.grantPutEventsTo(stateMachine.role);
  }
}
