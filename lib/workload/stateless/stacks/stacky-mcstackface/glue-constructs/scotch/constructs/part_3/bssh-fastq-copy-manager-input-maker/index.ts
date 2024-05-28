import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import path from 'path';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import { WorkflowRunStateChangeInternalInputMakerConstruct } from '../../../../../../../../components/event-workflowrunstatechange-internal-to-inputmaker-sfn';

/*
Part 3

* Input Event Source: `orcabus.workflowmanager`
* Input Event DetailType: `orcabus.workflowrunstatechange`
* Input Event status: `complete`


* Output Event source: `orcabus.bsshfastqcopyinputeventglue`
* Output Event DetailType: `orcabus.workflowrunstatechange`
* Output Event status: `complete`


* The BsshFastqCopyManagerInputMaker Construct
  * Subscribes to the BCLConvertManagerEventHandler Stack outputs and creates the input for the BSSHFastqCopyManager
  * Pushes an event payload of the input for the BsshFastqCopyManagerReadyEventSubmitter

*/

export interface bsshFastqCopyManagerInputMakerConstructProps {
  tableObj: dynamodb.ITableV2;
  outputUriPrefixSsmParameterObj: ssm.IStringParameter;
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
  eventBusObj: events.IEventBus;
}

export class bsshFastqCopyManagerInputMakerConstruct extends Construct {
  public readonly bsshFastqCopyManagerInputMakerEventMap = {
    prefix: 'bsshFastqCopyMaker',
    tablePartition: 'bssh_fastq_copy',
    triggerSource: 'orcabus.workflowmanager',
    triggerStatus: 'succeeded',
    triggerDetailType: 'workflowRunStateChange',
    triggerWorkflowName: 'bclconvert',
    outputSource: 'orcabus.bsshfastqcopyinputeventglue',
    outputStatus: 'ready',
    payloadVersion: '2024.05.24',
    workflowName: 'bsshFastqCopy',
    workflowVersion: '2024.05.24',
  };

  constructor(scope: Construct, id: string, props: bsshFastqCopyManagerInputMakerConstructProps) {
    super(scope, id);

    /*
    Part 1: Build the internal sfn
    */
    const inputMakerSfn = new sfn.StateMachine(this, 'bssh_fastq_copy_manager_input_maker', {
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_function_templates',
          'bssh_fastq_copy_maker_data_input_maker.asl.json'
        )
      ),
      definitionSubstitutions: {
        __table_name__: props.tableObj.tableName,
        __bclconvert_output_uri_ssm_parameter_name__:
          props.outputUriPrefixSsmParameterObj.parameterName,
      },
    });

    /*
    Part 2: Grant the internal sfn permissions to access the ssm parameter
    */
    props.outputUriPrefixSsmParameterObj.grantRead(inputMakerSfn.role);

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
        lambdaPrefix: this.bsshFastqCopyManagerInputMakerEventMap.prefix,
        payloadVersion: this.bsshFastqCopyManagerInputMakerEventMap.payloadVersion,
        stateMachinePrefix: this.bsshFastqCopyManagerInputMakerEventMap.prefix,

        /*
        Table objects
        */
        tableObj: props.tableObj,
        tablePartitionName: this.bsshFastqCopyManagerInputMakerEventMap.tablePartition,

        /*
        Event Triggers
        */
        eventBusObj: props.eventBusObj,
        triggerSource: this.bsshFastqCopyManagerInputMakerEventMap.triggerSource,
        triggerStatus: this.bsshFastqCopyManagerInputMakerEventMap.triggerStatus,
        triggerWorkflowName: this.bsshFastqCopyManagerInputMakerEventMap.triggerWorkflowName,
        outputSource: this.bsshFastqCopyManagerInputMakerEventMap.outputSource,
        workflowName: this.bsshFastqCopyManagerInputMakerEventMap.workflowName,
        workflowVersion: this.bsshFastqCopyManagerInputMakerEventMap.workflowVersion,
      }
    );
  }
}
