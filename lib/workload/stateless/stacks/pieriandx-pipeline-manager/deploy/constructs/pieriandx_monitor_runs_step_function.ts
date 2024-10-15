import { Construct } from 'constructs';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as events from 'aws-cdk-lib/aws-events';
import { DefinitionBody } from 'aws-cdk-lib/aws-stepfunctions';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { Duration } from 'aws-cdk-lib';
import * as events_targets from 'aws-cdk-lib/aws-events-targets';

interface PieriandxMonitorRunsStepFunctionConstructProps {
  /* Stack Objects */
  dynamodbTableObj: dynamodb.ITableV2;

  /* Workflow */
  workflowName: string;
  workflowVersion: string;

  /* Lambdas paths */
  getInformaticsjobAndReportStatusLambdaObj: PythonFunction;
  generateOutputPayloadDataLambdaObj: PythonFunction;

  /* Step function templates */
  launchPieriandxMonitorRunsStepfunctionTemplatePath: string;

  /* SSM Parameters */
  pierianDxBaseUrlSsmParameterObj: ssm.IStringParameter;

  /* Event Bus */
  eventBusName: string;
  eventDetailType: string;
  eventSource: string;
  payloadVersion: string;

  /* Custom */
  prefix: string;
}

export class PieriandxMonitorRunsStepFunctionStateMachineConstruct extends Construct {
  public readonly stateMachineObj: sfn.IStateMachine;

  constructor(scope: Construct, id: string, props: PieriandxMonitorRunsStepFunctionConstructProps) {
    super(scope, id);

    // Specify the statemachine and replace the arn placeholders with the lambda arns defined above
    const stateMachine = new sfn.StateMachine(
      this,
      'pieriandx_launch_step_functions_state_machine',
      {
        // State Machine Name
        stateMachineName: `${props.prefix}-monitor-runs-sfn`,
        // defintiontemplate
        definitionBody: DefinitionBody.fromFile(
          props.launchPieriandxMonitorRunsStepfunctionTemplatePath
        ),
        // definitionSubstitutions
        definitionSubstitutions: {
          /* Tables */
          __table_name__: props.dynamodbTableObj.tableName,

          /* Workflow Name */
          __workflow_name__: props.workflowName,
          __workflow_version__: props.workflowVersion,

          /* Lambdas */
          __get_current_job_status_lambda_function_arn__:
            props.getInformaticsjobAndReportStatusLambdaObj.currentVersion.functionArn,
          __generate_data_payload_lambda_function_arn__:
            props.generateOutputPayloadDataLambdaObj.currentVersion.functionArn,

          /* Hardcoded ssm parameters */
          __pieriandx_base_url__: props.pierianDxBaseUrlSsmParameterObj.stringValue,

          /* Event Bus Name */
          __event_bus_name__: props.eventBusName,
          __event_detail_type__: props.eventDetailType,
          __event_source__: props.eventSource,
          __payload_version__: props.payloadVersion,
        },
      }
    );

    // Grant lambda invoke permissions to the state machine
    [
      props.getInformaticsjobAndReportStatusLambdaObj,
      props.generateOutputPayloadDataLambdaObj,
    ].forEach((lambdaFunction) => {
      lambdaFunction.currentVersion.grantInvoke(stateMachine);
    });

    // Get the event bus from the event bus name
    const eventBusObj = events.EventBus.fromEventBusName(this, 'eventBus', props.eventBusName);

    // Allow state machine to read/write to dynamodb table
    props.dynamodbTableObj.grantReadWriteData(stateMachine);

    // Add rule for this sfn to run every 5 minutes
    const rule = new events.Rule(this, 'rule', {
      ruleName: `${props.prefix}-pieriandx-monitor-runs-rule`,
      schedule: events.Schedule.rate(Duration.minutes(5)),
    });

    // Add permissions to the state machine to send events to the event bus
    eventBusObj.grantPutEventsTo(stateMachine);

    /* Add rule as a target to the state machine */
    rule.addTarget(
      new events_targets.SfnStateMachine(stateMachine, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );

    // Set outputs
    this.stateMachineObj = stateMachine;
  }
}
