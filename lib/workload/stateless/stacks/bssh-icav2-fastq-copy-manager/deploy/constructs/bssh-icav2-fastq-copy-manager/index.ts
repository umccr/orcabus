import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import * as events_targets from 'aws-cdk-lib/aws-events-targets';
import { DefinitionBody } from 'aws-cdk-lib/aws-stepfunctions';

import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';

interface BsshIcav2FastqCopyStateMachineConstructProps {
  prefix: string; // bsshFastqCopy
  icav2CopyBatchStateMachineObj: sfn.IStateMachine;
  icav2JwtSsmParameterObj: secretsmanager.ISecret;
  eventBusObj: events.IEventBus; // Orcabus main event
  bclconvertSuccessEventHandlerLambdaObj: PythonFunction; // __dirname + '/../../../lambdas/bclconvert_success_event_handler'
  // execution_check_status_lambda_path: string; // __dirname + '../lambdas/check_execution_completion'
  workflowDefinitionBodyPath: string; // __dirname + '../step_functions_templates/bclconvert_success_event_state_machine.json'
  // Event handling //
  detailType: string; // WorkflowRunStateChange
  serviceVersion: string; // 2024.05.15
  triggerLaunchSource: string; // orcabus.workflowmanager
  internalEventSource: string; // orcabus.bsshfastqcopy
  workflowName: string; // bsshFastqCopy
  workflowVersion: string; // 1.0.0
}

export class BsshIcav2FastqCopyStateMachineConstruct extends Construct {
  public readonly bsshIcav2FastqCopyEventMap = {
    triggerSource: 'orcabus.workflowmanager',
    triggerDetailType: 'WorkflowRunStateChange',
    triggerDetailStatus: 'READY',
  };

  constructor(scope: Construct, id: string, props: BsshIcav2FastqCopyStateMachineConstructProps) {
    super(scope, id);

    // Add icav2 secrets permissions to lambda
    props.icav2JwtSsmParameterObj.grantRead(
      <iam.IRole>props.bclconvertSuccessEventHandlerLambdaObj.currentVersion.role
    );

    // Specify the statemachine and replace the arn placeholders with the lambda arns defined above
    const stateMachine = new sfn.StateMachine(this, 'bssh_fastq_copy_state_machine', {
      stateMachineName: `${props.prefix}-run-icav2-fastq-copy`,
      // defintiontemplate
      definitionBody: DefinitionBody.fromFile(props.workflowDefinitionBodyPath),
      // definitionSubstitutions
      definitionSubstitutions: {
        __bclconvert_success_event_lambda_arn__:
          props.bclconvertSuccessEventHandlerLambdaObj.currentVersion.functionArn,
        __copy_batch_data_state_machine_arn__: props.icav2CopyBatchStateMachineObj.stateMachineArn,
        __eventbus_name__: props.eventBusObj.eventBusName,
        __detail_type__: props.detailType,
        __event_source__: props.internalEventSource,
        __workflow_name__: props.workflowName,
        __workflow_version__: props.workflowVersion,
        __payload_version__: props.serviceVersion,
      },
    });

    // Add execution permissions to stateMachine role
    props.bclconvertSuccessEventHandlerLambdaObj.currentVersion.grantInvoke(stateMachine.role);

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
        source: [this.bsshIcav2FastqCopyEventMap.triggerSource],
        detailType: [this.bsshIcav2FastqCopyEventMap.triggerDetailType],
        detail: {
          status: [{ 'equals-ignore-case': this.bsshIcav2FastqCopyEventMap.triggerDetailStatus }],
          workflowName: [{ 'equals-ignore-case': props.workflowName }],
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
