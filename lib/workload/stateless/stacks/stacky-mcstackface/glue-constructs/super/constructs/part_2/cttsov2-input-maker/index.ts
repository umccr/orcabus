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
  inputMakerTableObj: dynamodb.ITableV2;
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
  outputUriSsmParameterObj: ssm.IStringParameter;
  logsUriSsmParameterObj: ssm.IStringParameter;
  cacheUriSsmParameterObj: ssm.IStringParameter;
  eventBusObj: events.IEventBus;
}

export class cttsov2InputMakerConstruct extends Construct {
  public readonly cttsov2InputMakerEventMap = {
    prefix: 'cttsov2InputMaker',
    tablePartition: 'cttso_v2',
    triggerSource: 'orcabus.cttsov2inputeventglue',
    triggerStatus: 'draft',
    triggerDetailType: 'WorkflowDraftRunStateChange',
    triggerWorkflowName: 'cttsov2',
    outputSource: 'orcabus.cttsov2inputeventglue',
    outputStatus: 'ready',
    payloadVersion: '2024.05.24',
    workflowName: 'cttsov2',
    workflowVersion: '2.5.0',
  };

  constructor(scope: Construct, id: string, props: cttsov2InputMakerConstructProps) {
    super(scope, id);
    /*
    Part 1: Build the internal sfn
    */
    const inputMakerSfn = new sfn.StateMachine(this, 'cttsov2_input_maker', {
      stateMachineName: `${this.cttsov2InputMakerEventMap.prefix}-input-maker-glue-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(__dirname, 'step_function_templates', 'generate_cttsov2_event_maker.asl.json')
      ),
      definitionSubstitutions: {
        __table_name__: props.inputMakerTableObj.tableName,
        __input_maker_type__: this.cttsov2InputMakerEventMap.tablePartition,
        __analysis_logs_uri_ssm_parameter_name__: props.logsUriSsmParameterObj.parameterName,
        __analysis_output_uri_ssm_parameter_name__: props.outputUriSsmParameterObj.parameterName,
        __analysis_cache_uri_ssm_parameter_name__: props.cacheUriSsmParameterObj.parameterName,
        __icav2_project_id_and_name_ssm_parameter_name__:
          props.icav2ProjectIdSsmParameterObj.parameterName,
      },
    });

    /*
    Part 2: Grant the internal sfn permissions
    */

    // Access to ssm parameters
    [
      props.outputUriSsmParameterObj,
      props.icav2ProjectIdSsmParameterObj,
      props.cacheUriSsmParameterObj,
      props.logsUriSsmParameterObj,
    ].forEach((ssmParameterObj) => {
      ssmParameterObj.grantRead(inputMakerSfn.role);
    });

    // Read/Write access to the tables
    props.inputMakerTableObj.grantReadWriteData(inputMakerSfn.role);

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
        tableObj: props.inputMakerTableObj,
        tablePartitionName: this.cttsov2InputMakerEventMap.tablePartition,

        /*
        Event Triggers
        */
        eventBusObj: props.eventBusObj,
        triggerDetailType: this.cttsov2InputMakerEventMap.triggerDetailType,
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
