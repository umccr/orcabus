import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import path from 'path';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import { WorkflowRunStateChangeInternalInputMakerConstruct } from '../../../../../../../components/event-workflowrunstatechange-internal-to-inputmaker-sfn';

/*
Part 1

Input Event Source: `orcabus.workflowmanager`
Input Event DetailType: `WorkflowRunStateChange`
Input Event status: `complete`

Output Event source: `orcabus.bclconvertinteropqcinputeventglue`
Output Event DetailType: `WorkflowRunStateChange`
Output Event status: `complete`


* The BCLConvertInteropQCInputMaker Construct
  * Subscribes to the BSSHFastqCopyManagerEventHandler Construct outputs and creates the input for the BCLConvertInteropQC
  * Pushes an event payload of the input for the BCLConvertInteropQCReadyEventSubmitter


*/

export interface BclconvertInteropqcInputMakerConstructProps {
  tableObj: dynamodb.ITableV2;
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
  analysisOutputUriSsmParameterObj: ssm.IStringParameter;
  analysisLogsUriSsmParameterObj: ssm.IStringParameter;
  eventBusObj: events.IEventBus;
}

export class BclconvertInteropqcInputMakerConstruct extends Construct {
  public readonly bclconvertInteropqcInputMakerEventMap = {
    prefix: 'bclInterOpQCInputMaker',
    tablePartition: 'bclconvert_interop_qc',
    triggerSource: 'orcabus.workflowmanager',
    triggerStatus: 'succeeded',
    triggerDetailType: 'WorkflowRunStateChange',
    triggerWorkflowName: 'bsshFastqCopy',
    outputSource: 'orcabus.bclconvertinteropqcinputeventglue',
    outputStatus: 'ready',
    payloadVersion: '2024.05.24',
    workflowName: 'bclconvert_interop_qc',
    workflowVersion: '1.3.1--1.21__20240410040204',
  };

  constructor(scope: Construct, id: string, props: BclconvertInteropqcInputMakerConstructProps) {
    super(scope, id);

    /*
        Part 1: Build the internal sfn
        */
    const inputMakerSfn = new sfn.StateMachine(this, 'bclconvert_interopqc_input_maker', {
      stateMachineName: `${this.bclconvertInteropqcInputMakerEventMap.prefix}-input-maker-glue`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(__dirname, 'step_function_templates', 'generate_interopqc_event_maker.asl.json')
      ),
      definitionSubstitutions: {
        __table_name__: props.tableObj.tableName,
        __input_maker_type__: this.bclconvertInteropqcInputMakerEventMap.tablePartition,
        __analysis_logs_uri_ssm_parameter_name__:
          props.analysisLogsUriSsmParameterObj.parameterName,
        __analysis_output_uri_ssm_parameter_name__:
          props.analysisOutputUriSsmParameterObj.parameterName,
        __icav2_project_id_and_name_ssm_parameter_name__:
          props.icav2ProjectIdSsmParameterObj.parameterName,
      },
    });

    /*
    Part 2: Grant the internal sfn permissions
    */

    // access the ssm parameter
    [
      props.analysisOutputUriSsmParameterObj,
      props.icav2ProjectIdSsmParameterObj,
      props.analysisLogsUriSsmParameterObj,
    ].forEach((ssmParameterObj) => {
      ssmParameterObj.grantRead(inputMakerSfn.role);
    });

    // access the dynamodb table
    props.tableObj.grantReadWriteData(inputMakerSfn.role);

    /*
    Part 3: Build the external sfn
    */
    new WorkflowRunStateChangeInternalInputMakerConstruct(
      this,
      'bclconvert_interop_qc_input_maker_external',
      {
        /*
        Set Input StateMachine Object
        */
        inputStateMachineObj: inputMakerSfn,
        lambdaPrefix: this.bclconvertInteropqcInputMakerEventMap.prefix,
        payloadVersion: this.bclconvertInteropqcInputMakerEventMap.payloadVersion,
        stateMachinePrefix: this.bclconvertInteropqcInputMakerEventMap.prefix,

        /*
        Table objects
        */
        tableObj: props.tableObj,
        tablePartitionName: this.bclconvertInteropqcInputMakerEventMap.tablePartition,

        /*
        Event Triggers
        */
        eventBusObj: props.eventBusObj,
        triggerSource: this.bclconvertInteropqcInputMakerEventMap.triggerSource,
        triggerStatus: this.bclconvertInteropqcInputMakerEventMap.triggerStatus,
        triggerWorkflowName: this.bclconvertInteropqcInputMakerEventMap.triggerWorkflowName,
        outputSource: this.bclconvertInteropqcInputMakerEventMap.outputSource,
        workflowName: this.bclconvertInteropqcInputMakerEventMap.workflowName,
        workflowVersion: this.bclconvertInteropqcInputMakerEventMap.workflowVersion,
      }
    );
  }
}
