import { Duration } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { DefinitionBody } from 'aws-cdk-lib/aws-stepfunctions';
import * as sfn_tasks from 'aws-cdk-lib/aws-stepfunctions-tasks';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import * as events from 'aws-cdk-lib/aws-events';
import { get } from 'http';

interface Icav2EventTranslatorLaunchStepFunctionConstructProps {
  // Stack objects
  dynamodb_table_obj: dynamodb.ITableV2; // dynamodb table object
  event_bus_obj: events.IEventBus; // event bus object

  // Lambda Paths
  launch_icav2_event_translator_lambda_path: string; // __dirname + '/../../../lambdas'

  // Step function object list
  ssm_parameter_obj_list: ssm.IStringParameter[]; // List of parameters the workflow session state machine will need access to
}

export class Icav2EventTranslatorLaunchStepFunctionStateMachineConstruct extends Construct {
  public readonly icav2_event_translator_launch_statemachine_arn: string;

  constructor(
    scope: Construct,
    id: string,
    props: Icav2EventTranslatorLaunchStepFunctionConstructProps
  ) {
    super(scope, id);

    /*
    Aim of this construct is to generate a cloudformation construct with the following attributes

    - A step function state machine that will launch the icav2_event_translator pipeline

    These state machines will be generated from the definition chain (or templates) provided in the props

    We generate an internal event to main event bus for any subscribing services to act on.
    We update the dynamodb table at the end of the process for analysis of step functions.
    */

    // launch_icav2_event_translator_ lambda
    const launch_icav2_event_translator_lambda = new PythonFunction(
      this,
      'launch_icav2_event_translator_lambda_python_function',
      {
        entry: props.launch_icav2_event_translator_lambda_path,
        runtime: lambda.Runtime.PYTHON_3_11,
        index: 'icav2_event_translator_handler.py',
        handler: 'icav2_event_translator_handler',
        memorySize: 1024,
        timeout: Duration.seconds(60),
      }
    );

    // Add each of the ssm parameters to the lambda role policy
    props.ssm_parameter_obj_list.forEach((ssm_parameter_obj) => {
      ssm_parameter_obj.grantRead(<iam.IRole>launch_icav2_event_translator_lambda.role);
    });

    // Specify the statemachine
    const launchStateMachine = new sfn.StateMachine(
      this,
      'icav2_event_translator_step_functions_state_machine',
      {
        // defintion template
        definitionBody: DefinitionBody.fromChainable(
          this.build_state_machine_definition_body(
            launch_icav2_event_translator_lambda,
            props.event_bus_obj,
            props.dynamodb_table_obj
          )
        ),
      }
    );

    // Add lambda execution permissions to launch stateMachine
    launch_icav2_event_translator_lambda.grantInvoke(<iam.IRole>launchStateMachine.role);

    // Add dynamodb permissions to stateMachines
    props.dynamodb_table_obj.grantReadWriteData(launchStateMachine.role);

    props.event_bus_obj.grantPutEventsTo(launchStateMachine.role);

    // Set outputs
    this.icav2_event_translator_launch_statemachine_arn = launchStateMachine.stateMachineArn;
  }

  private build_state_machine_definition_body(
    lambdaFunction: PythonFunction,
    eventBus: events.IEventBus,
    table: dynamodb.ITableV2
  ): sfn.IChainable {
    const lambdaTask = new sfn_tasks.LambdaInvoke(
      this,
      'launch_icav2_event_translator_lambda_task',
      {
        //@ts-ignore (as conflict between PythonFunction and IFunction)
        lambdaFunction,
        retryOnServiceExceptions: true,
      }
    );

    const generateInternalEventTask = new sfn_tasks.EventBridgePutEvents(
      this,
      'generate_orcabus_internal_event_task',
      {
        entries: [
          {
            // need to be tested with the acutal event
            detail: sfn.TaskInput.fromJsonPathAt('$.Payload'),
            eventBus: eventBus,
            detailType: 'orcabus_internal_event',
            source: 'icav2_event',
          },
        ],
      }
    );

    const recordEventInfoTask = new sfn_tasks.DynamoPutItem(
      this,
      'create_dynamodb_table_item_task',
      {
        table,
        item: {
          projectId: sfn_tasks.DynamoAttributeValue.fromString(
            sfn.JsonPath.stringAt('$.Payload.projectId')
          ),
          analysisId: sfn_tasks.DynamoAttributeValue.fromString(
            sfn.JsonPath.stringAt('$.Payload.analysisId')
          ),
          instrumentRunId: sfn_tasks.DynamoAttributeValue.fromString(
            sfn.JsonPath.stringAt('$.Payload.instrumentRunId')
          ),
          timeCreated: sfn_tasks.DynamoAttributeValue.fromString(new Date().toLocaleTimeString()), // get current time
          status: sfn_tasks.DynamoAttributeValue.fromString('Event translated successfully.'),
        },
      }
    );

    // parallel functions for recording event information and put new internal event to event bus
    const parallelFunctions = new sfn.Parallel(this, 'Parallel');
    parallelFunctions.branch(recordEventInfoTask).branch(generateInternalEventTask);

    const recordEventResultTask = new sfn_tasks.DynamoUpdateItem(
      this,
      'update_dynamodb_table_item_task',
      {
        table,
        key: {
          id: sfn_tasks.DynamoAttributeValue.fromString(sfn.JsonPath.stringAt('$.Payload.id')),
        },
        updateExpression: 'SET #status = :status',
        expressionAttributeNames: { '#status': 'status' },
        expressionAttributeValues: {
          ':status': sfn_tasks.DynamoAttributeValue.fromString(
            'Translated event pushed to event bus successfully.'
          ),
        },
      }
    );

    return sfn.Chain.start(lambdaTask).next(parallelFunctions).next(recordEventResultTask);
  }
}
