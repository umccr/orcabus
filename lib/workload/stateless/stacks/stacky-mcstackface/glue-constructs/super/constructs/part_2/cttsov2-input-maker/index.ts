import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import path from 'path';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import { WorkflowRunStateChangeInternalInputMakerConstruct } from '../../../../../../../../components/event-workflowrunstatechange-internal-to-inputmaker-sfn';

/*
Part 2

Output Event source: `orcabus.cttsov2inputeventglue`
Output Event DetailType: `WorkflowRunStateChange`
Output Event status: `awaitinginput`


Output Event source: `orcabus.cttsov2inputeventglue`
Output Event DetailType: `WorkflowRunStateChange`
Output Event status: `ready`

* The ctTSOv2InputMaker, subscribes to the cttsov2 input event glue (itself) and generates a ready event for the ctTSOv2ReadySfn
  * For the cttso v2 workflow we require a samplesheet, a set of fastq list rows (provided in the last step)
  * However, in order to be 'ready' we need to use a few more variables such as
    * icaLogsUri,
    * analysisOuptutUri
    * cacheUri
    * projectId
    * userReference



*/

export interface cttsov2InputMakerConstructProps {
  tableObj: dynamodb.ITableV2;
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
  outputUriPrefixSsmParameterObj: ssm.IStringParameter;
  cacheUriPrefixSsmParameterObj: ssm.IStringParameter;
  eventBusObj: events.IEventBus;
}

export class cttsov2InputMakerConstruct extends Construct {
  public readonly cttsov2InputMakerEventMap = {
    prefix: 'cttsov2InputMaker',
    tablePartition: 'cttso_v2',
    triggerSource: 'orcabus.cttsov2inputeventglue',
    triggerStatus: 'awaitinginput',
    triggerDetailType: 'WorkflowRunStateChange',
    triggerWorkflowName: 'cttsov2',
    outputSource: 'orcabus.cttsov2inputeventglue',
    outputStatus: 'ready',
    payloadVersion: '2024.05.24',
    workflowName: 'cttsov2',
    workflowVersion: '2.1.1',
  };

  constructor(scope: Construct, id: string, props: cttsov2InputMakerConstructProps) {
    super(scope, id);
    /*
        Part 1: Build the internal sfn
        */
    const inputMakerSfn = new sfn.StateMachine(this, 'cttsov2_input_maker', {
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(__dirname, 'step_function_templates', 'generate_cttsov2_event_maker.asl.json')
      ),
      definitionSubstitutions: {
        __table_name__: props.tableObj.tableName,
        __input_maker_type__: this.cttsov2InputMakerEventMap.tablePartition,
        __cttsov2_output_uri_ssm_parameter_name__:
          props.outputUriPrefixSsmParameterObj.parameterName,
        __cttsov2_cache_uri_ssm_parameter_name__: props.cacheUriPrefixSsmParameterObj.parameterName,
        __icav2_project_id_and_name_ssm_parameter_name__:
          props.icav2ProjectIdSsmParameterObj.parameterName,
      },
    });

    /*
    Part 2: Grant the internal sfn permissions to access the ssm parametera
    */
    [
      props.outputUriPrefixSsmParameterObj,
      props.icav2ProjectIdSsmParameterObj,
      props.cacheUriPrefixSsmParameterObj,
    ].forEach((ssmParameterObj) => {
      ssmParameterObj.grantRead(inputMakerSfn.role);
    });

    /*
        Part 3: Build the external sfn
        */
    new WorkflowRunStateChangeInternalInputMakerConstruct(
      this,
      'bssh_fastq_copy_manager_input_maker_external',
      {
        /*
                Set Input StateMachine Object
                */
        inputStateMachineObj: inputMakerSfn,
        lambdaPrefix: this.cttsov2InputMakerEventMap.prefix,
        payloadVersion: this.cttsov2InputMakerEventMap.payloadVersion,
        stateMachinePrefix: this.cttsov2InputMakerEventMap.prefix,

        /*
                Table objects
                */
        tableObj: props.tableObj,
        tablePartitionName: this.cttsov2InputMakerEventMap.tablePartition,

        /*
                Event Triggers
                */
        eventBusObj: props.eventBusObj,
        triggerSource: this.cttsov2InputMakerEventMap.triggerSource,
        triggerStatus: this.cttsov2InputMakerEventMap.triggerStatus,
        triggerWorkflowName: this.cttsov2InputMakerEventMap.triggerWorkflowName,
        outputSource: this.cttsov2InputMakerEventMap.outputSource,
        workflowName: this.cttsov2InputMakerEventMap.workflowName,
        workflowVersion: this.cttsov2InputMakerEventMap.workflowVersion,
      }
    );
  }
}
