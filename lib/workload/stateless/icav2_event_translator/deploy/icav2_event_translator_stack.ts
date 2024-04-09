import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { Icav2EventTranslatorLaunchStepFunctionStateMachineConstruct } from './constructs/icav2_event_translator_step_function';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as events from 'aws-cdk-lib/aws-events';

interface Icav2EventTranslatorLaunchStateMachineStackProps extends cdk.StackProps {
  dynamodb_name_ssm_parameter_path: string; // "/umccr/orcabus/stateful/icav2_event_translator_dynamo_db/translator_table_name"
  eventbus_name_ssm_parameter_path: string; // "/umccr/orcabus/stateful/eventbridge"
  ssm_parameter_list: string[]; // List of parameters the workflow session state machine will need access to
  icav2_event_translator_launch_state_machine_ssm_parameter_path: string; // "/icav2/umccr-prod/icav2_event_translator_launch_statemachine_arn"
}

export class Icav2EventTranslatorLaunchStateMachineStack extends cdk.Stack {
  public readonly icav2_event_translator_launch_state_machine_arn: string;
  public readonly icav2_event_translator_launch_state_machine_ssm_parameter_path: string;

  constructor(
    scope: Construct,
    id: string,
    props: Icav2EventTranslatorLaunchStateMachineStackProps
  ) {
    super(scope, id, props);

    // Get dynamodb table for construct
    const dynamic_table_name_str = ssm.StringParameter.fromStringParameterName(
      this,
      'dynamic_table_name',
      props.dynamodb_name_ssm_parameter_path
    ).stringValue;
    const dynamodb_table_obj = dynamodb.TableV2.fromTableName(
      this,
      'Icav2EventTranslatorDynamoDBTable',
      dynamic_table_name_str
    );

    // Get event bus for construct
    const event_bus_name_str = ssm.StringParameter.fromStringParameterName(
      this,
      'event_bus_name',
      props.eventbus_name_ssm_parameter_path
    ).stringValue;

    const event_bus_obj = events.EventBus.fromEventBusName(this, 'event_bus', event_bus_name_str);

    // Set ssm parameter object list
    const ssm_parameter_obj_list = props.ssm_parameter_list.map((ssm_parameter_path: string) =>
      ssm.StringParameter.fromStringParameterName(this, ssm_parameter_path, ssm_parameter_path)
    );

    // Create the state machines and lambdas.
    // Connect permissions for statemachines to access the dynamodb table and launch lambda functions
    // Connect permissions for lambdas to access the secrets manager
    const icav2_event_translator_launch_state_machine =
      new Icav2EventTranslatorLaunchStepFunctionStateMachineConstruct(this, id, {
        // Stack objects
        dynamodb_table_obj: dynamodb_table_obj,
        event_bus_obj: event_bus_obj,
        launch_icav2_event_translator_lambda_path: __dirname + '/../lambdas', // __dirname + '/../../../lambdas/'
        ssm_parameter_obj_list: ssm_parameter_obj_list, // List of parameters the workflow session state machine will need access to
      });

    // Set outputs
    this.icav2_event_translator_launch_state_machine_arn =
      icav2_event_translator_launch_state_machine.icav2_event_translator_launch_statemachine_arn;
    this.icav2_event_translator_launch_state_machine_ssm_parameter_path =
      props.icav2_event_translator_launch_state_machine_ssm_parameter_path;

    this.set_ssm_parameter_obj_for_state_machine(
      icav2_event_translator_launch_state_machine.icav2_event_translator_launch_statemachine_arn
    );
  }

  private set_ssm_parameter_obj_for_state_machine(state_machine_arn: string): ssm.StringParameter {
    /*
    Generate the ssm parameter for the state machine arn
    */
    return new ssm.StringParameter(this, 'state_machine_arn_ssm_parameter', {
      parameterName: this.icav2_event_translator_launch_state_machine_ssm_parameter_path,
      stringValue: state_machine_arn,
    });
  }
}
