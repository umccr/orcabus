import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as events from 'aws-cdk-lib/aws-events';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { OraDecompressionConstruct } from '../../../../components/ora-file-decompression-fq-pair-sfn';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import path from 'path';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';
import { NagSuppressions } from 'cdk-nag';

export interface OraDecompressionPipelineManagerConfig {
  /* Stack essentials */
  eventBusName: string;
  detailType: string;
  triggerEventSource: string;
  outputEventSource: string;
  stateMachinePrefix: string;
  /* ICAv2 Pipeline analysis essentials */
  icav2TokenSecretId: string; // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
}

export type OraDecompressionManagerStackProps = OraDecompressionPipelineManagerConfig &
  cdk.StackProps;

export class OraDecompressionManagerStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: OraDecompressionManagerStackProps) {
    super(scope, id, props);

    // Get ICAv2 Access token secret object for construct
    const icav2AccessTokenSecretObj = secretsManager.Secret.fromSecretNameV2(
      this,
      'icav2_secrets_object',
      props.icav2TokenSecretId
    );

    // Get the copy batch state machine name
    const oraDecompressionSfnConstruct = new OraDecompressionConstruct(
      this,
      'ora_decompression_sfn_construct',
      {
        sfnPrefix: props.stateMachinePrefix,
        icav2AccessTokenSecretId: icav2AccessTokenSecretObj.secretName,
      }
    );

    // Generate the parent step function
    const oraManagerSfn = new sfn.StateMachine(this, 'state_machine', {
      stateMachineName: `${props.stateMachinePrefix}-event-handler-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          '../step_functions_templates/ora_decompression_manager_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* Event */
        __event_bus_name__: props.eventBusName,
        __detail_type__: props.detailType,
        __source__: props.outputEventSource,
        /* Decompression SFN */
        __ora_decompression_sfn_arn__: oraDecompressionSfnConstruct.sfnObject.stateMachineArn,
      },
    });

    /* Grant the state machine access to invoke the internal launch sfn machine */
    oraDecompressionSfnConstruct.sfnObject.grantStartExecution(oraManagerSfn);
    oraDecompressionSfnConstruct.sfnObject.grantRead(oraManagerSfn);

    // Because we run a nested state machine, we need to add the permissions to the state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    oraManagerSfn.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );

    // https://docs.aws.amazon.com/step-functions/latest/dg/connect-stepfunctions.html#sync-async-iam-policies
    // Polling requires permission for states:DescribeExecution
    NagSuppressions.addResourceSuppressions(
      oraManagerSfn,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'grantRead uses asterisk at the end of executions, as we need permissions for all execution invocations',
        },
      ],
      true
    );

    // Create a rule to trigger the state machine
    const rule = new events.Rule(this, 'rule', {
      eventBus: events.EventBus.fromEventBusName(this, 'event_bus', props.eventBusName),
      eventPattern: {
        source: [props.triggerEventSource],
        detailType: [props.detailType],
      },
    });

    // Add target to the rule
    rule.addTarget(
      new eventsTargets.SfnStateMachine(oraManagerSfn, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );
  }
}
