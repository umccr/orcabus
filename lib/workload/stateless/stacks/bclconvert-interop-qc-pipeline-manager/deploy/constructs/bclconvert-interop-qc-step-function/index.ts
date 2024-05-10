import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { DefinitionBody } from 'aws-cdk-lib/aws-stepfunctions';

import { Icav2AnalysisEventHandlerConstruct } from '../../../../../../components/dynamodb-icav2-handle-event-change-sfn';
import { WfmWorkflowStateChangeIcav2ReadyEventHandlerConstruct } from '../../../../../../components/dynamodb-icav2-ready-event-handler-sfn';

interface BclConvertInteropQcIcav2PipelineManagerConstructProps {
  // Stack objects
  dynamodbTableObj: dynamodb.ITableV2; // dynamodb table object
  icav2AccessTokenSecretObj: secretsManager.ISecret; // "ICAv2Jwticav2-credentials-umccr-service-user-trial"
  pipelineIdSsmObj: ssm.IStringParameter; // "ICAv2PipelineId"
  // Step function template paths
  generateInputJsonSfnTemplatePath: string; // __dirname + '/../../../step_functions_templates/bclconvert_interop_qc_pipeline_manager.json'
  // Event handling
  eventBusName: string;
  icaEventPipeName: string;
  workflowType: string;
  workflowVersion: string;
  serviceVersion: string;
  triggerLaunchSource: string;
  internalEventSource: string;
  detailType: string;
  // StateMachineNames
  stateMachinePrefix: string;
}

export class BclConvertInteropQcIcav2PipelineConstruct extends Construct {
  public readonly handleWfmReadyEventStateMachineObj: string;
  public readonly handleIcav2EventStateMachineObj: string;

  constructor(
    scope: Construct,
    id: string,
    props: BclConvertInteropQcIcav2PipelineManagerConstructProps
  ) {
    super(scope, id);

    /*
    Aim of this construct is to generate a cloudformation construct with the following attributes

    1. A step function that listens to the 'ready' event from the WFM for bclconvert interop qc pipelines
    2. A step function that can take the parameters of the payload and convert these into an input json for the ICAv2 pipeline analysis
    3. A step function that listens to icav2 events and returns internal events to the WFM

    */

    const configure_inputs_sfn = new sfn.StateMachine(this, 'configure_inputs_sfn', {
      stateMachineName: `${props.stateMachinePrefix}-configure-inputs-json`,
      definitionBody: DefinitionBody.fromFile(props.generateInputJsonSfnTemplatePath),
      definitionSubstitutions: {
        __table_name__: props.dynamodbTableObj.tableName,
      },
    });

    // Configure inputs step function needs to read-write to the dynamodb table
    props.dynamodbTableObj.grantReadWriteData(configure_inputs_sfn.role);

    // Generate state machine for handling the 'ready' event
    const handle_wfm_ready_event_sfn = new WfmWorkflowStateChangeIcav2ReadyEventHandlerConstruct(
      this,
      'handle_wfm_ready_event',
      {
        tableName: props.dynamodbTableObj.tableName,
        stateMachineName: `${props.stateMachinePrefix}-wfm-ready-event-handler`,
        icav2AccessTokenSecretObj: props.icav2AccessTokenSecretObj,
        workflowPlatformType: 'cwl', // Hardcoded this pipeline is a CWL pipeline.
        detailType: props.detailType,
        eventBusName: props.eventBusName,
        triggerLaunchSource: props.triggerLaunchSource,
        internalEventSource: props.internalEventSource,
        generateInputsJsonSfn: configure_inputs_sfn,
        pipelineIdSsmPath: props.pipelineIdSsmObj.parameterName,
        workflowType: props.workflowType,
        workflowVersion: props.workflowVersion,
        serviceVersion: props.serviceVersion,
      }
    ).stateMachineObj;

    // Generate state machine for handling the external ICAv2 event
    const handle_external_icav2_event_sfn = new Icav2AnalysisEventHandlerConstruct(
      this,
      'handle_interop_qc_ready_event',
      {
        tableName: props.dynamodbTableObj.tableName,
        stateMachineName: `${props.stateMachinePrefix}-icav2-external-handler`,
        detailType: props.detailType,
        eventBusName: props.eventBusName,
        icaEventPipeName: props.icaEventPipeName,
        internalEventSource: props.internalEventSource,
        workflowType: props.workflowType,
        workflowVersion: props.workflowVersion,
        serviceVersion: props.serviceVersion,
      }
    ).stateMachineObj;
  }
}
