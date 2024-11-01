/*

Given a cttsov2 success event we need to

1. Generate a portal run id
2. Collect any data available from redcap for this given subject / library combination
3. Collect the project owner and project name configuration for pieriandx
4. Collect the cttsov2 outputs
5. Send the data to pieriandx for processing

*/

import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import path from 'path';
import { NagSuppressions } from 'cdk-nag';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import * as events from 'aws-cdk-lib/aws-events';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Duration } from 'aws-cdk-lib';

/*
Part 2

Input Event Source: `orcabus.workflowmanager`
Input Event DetailType: `WorkflowRunStateChange`
Input Event status: `COMPLETE`
Input Event Workflow Name: `cttsov2`

Output Event Source: `orcabus.tninputeventglue`
Output Event DetailType: `WorkflowRunStateChange`
Output Event status: `READY`
Output Event Workflow Name: `pieriandx`

* Subscribe to the wgts input event glue, library complete event. 
* Launch a draft event for the tumor normal pipeline if the libraries' subject has a complement library that is also complete
*/

export interface Cttsov2CompleteToPieriandxConstructProps {
  /* Events */
  eventBusObj: events.IEventBus;

  /* Tables */
  tableObj: dynamodb.ITableV2;

  /* Secrets */
  icav2AccessTokenSecretObj: secretsManager.ISecret;

  /* Extras */
  projectInfoSsmParameterObj: ssm.IStringParameter;
  redcapLambdaObj: lambda.IFunction;
}

export class Cttsov2CompleteToPieriandxConstruct extends Construct {
  public readonly PierianDxMap = {
    prefix: 'nails-cttsov2-complete-to-pdx',
    tablePartition: {
      subject: 'subject',
      library: 'library',
      fastq_list_row: 'fastq_list_row',
    },

    /* Input Rules */
    triggerSource: 'orcabus.workflowmanager',
    triggerStatus: 'succeeded',
    triggerWorkflowName: 'cttsov2',
    triggerDetailType: 'WorkflowRunStateChange',

    /* Output Events */
    eventDetailType: 'WorkflowRunStateChange',
    eventStatus: 'READY',
    outputSource: 'orcabus.pieriandxinputeventglue',
    payloadVersion: '2024.07.23',
    workflowName: 'pieriandx',
    workflowVersion: '2.1',

    /* Default values */
    defaultSpecimenCode: '122561005',
    defaultSpecimenLabel: 'primarySpecimen',
  };

  constructor(scope: Construct, id: string, props: Cttsov2CompleteToPieriandxConstructProps) {
    super(scope, id);

    /*
    Part 1: Build the lambdas
    */
    const generatePortalRunIdPyLambdaObj = new PythonFunction(
      this,
      'generatePortalRunIdPyLambdaObj',
      {
        entry: path.join(__dirname, '/lambdas/generate_portal_run_id_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'generate_portal_run_id.py',
        handler: 'handler',
      }
    );

    const getDataFromRedCapPyLambdaObj = new PythonFunction(this, 'getDataFromRedCapPyLambdaObj', {
      entry: path.join(__dirname, '/lambdas/get_data_from_redcap_py'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'get_data_from_redcap.py',
      handler: 'handler',
      timeout: Duration.seconds(60),
      memorySize: 2048,
    });

    const getDeidentifiedCaseMetadataPyLambdaObj = new PythonFunction(
      this,
      'getDeidentifiedCaseMetadataPyLambdaObj',
      {
        entry: path.join(__dirname, '/lambdas/get_deidentified_case_metadata_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'get_deidentified_case_metadata.py',
        handler: 'handler',
        memorySize: 1024,
      }
    );
    const getIdentifiedCaseMetadataPyLambdaObj = new PythonFunction(
      this,
      'getIdentifiedCaseMetadataPyLambdaObj',
      {
        entry: path.join(__dirname, '/lambdas/get_identified_case_metadata_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'get_identified_case_metadata.py',
        handler: 'handler',
        memorySize: 1024,
      }
    );
    const getPieriandxDataFilesPyLambdaObj = new PythonFunction(
      this,
      'getPieriandxDataFilesPyLambdaObj',
      {
        entry: path.join(__dirname, '/lambdas/get_pieriandx_data_files_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'get_pieriandx_data_files.py',
        handler: 'handler',
        timeout: Duration.seconds(300),
        environment: {
          ICAV2_ACCESS_TOKEN_SECRET_ID: props.icav2AccessTokenSecretObj.secretName,
        },
        memorySize: 1024,
      }
    );
    const getProjectInfoPyLambdaObj = new PythonFunction(this, 'getProjectInfoPyLambdaObj', {
      entry: path.join(__dirname, '/lambdas/get_project_info_py'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'get_project_info.py',
      handler: 'handler',
    });

    /*
    Handle lambda permissions
    */
    // FIXME - cannot get the 'current' version of an IFunction object
    NagSuppressions.addResourceSuppressions(getDataFromRedCapPyLambdaObj, [
      {
        id: 'AwsSolutions-IAM5',
        reason: 'Cannot get latest version of redcap lambda function ($LATEST) will not work',
      },
    ]);
    props.redcapLambdaObj.grantInvoke(getDataFromRedCapPyLambdaObj.currentVersion);
    getDataFromRedCapPyLambdaObj.addEnvironment(
      'REDCAP_LAMBDA_FUNCTION_NAME',
      props.redcapLambdaObj.functionName
    );

    // Allow the getPieriandxDataFilesPyLambdaObj to read the secret
    props.icav2AccessTokenSecretObj.grantRead(getPieriandxDataFilesPyLambdaObj.currentVersion);

    // Allow the getProjectInfoPyLambdaObj to read the ssm parameters
    props.projectInfoSsmParameterObj.grantRead(getProjectInfoPyLambdaObj.currentVersion);
    getProjectInfoPyLambdaObj.addEnvironment(
      'PIERIANDX_SAMPLE_CONFIGURATION_SSM_PARAMETER_NAME',
      props.projectInfoSsmParameterObj.parameterName
    );

    /*
    Part 2: Build the sfn
    */
    const inputMakerSfn = new sfn.StateMachine(this, 'cttsov2_outputs_to_pieriandx', {
      stateMachineName: `${this.PierianDxMap.prefix}-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates',
          'cttso_v2_outputs_to_pieriandx_ready_event_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* Event handlers */
        __event_bus_name__: props.eventBusObj.eventBusName,
        __event_detail_type__: this.PierianDxMap.eventDetailType,
        __event_source__: this.PierianDxMap.outputSource,
        __event_status__: this.PierianDxMap.eventStatus,
        __event_version__: this.PierianDxMap.payloadVersion,
        __workflow_name__: this.PierianDxMap.workflowName,
        __workflow_version__: this.PierianDxMap.workflowVersion,
        __workflow_version_sub__: this.PierianDxMap.workflowVersion.replace(/\./g, '-'),

        /* Lambdas */
        __generate_portal_run_id_lambda_function_arn__:
          generatePortalRunIdPyLambdaObj.currentVersion.functionArn,
        __get_deidentified_case_metadata_lambda_function_arn__:
          getDeidentifiedCaseMetadataPyLambdaObj.currentVersion.functionArn,
        __get_identified_case_metadata_lambda_function_arn__:
          getIdentifiedCaseMetadataPyLambdaObj.currentVersion.functionArn,
        __get_pieriandx_project_pathway_mapping_lambda_function_arn__:
          getProjectInfoPyLambdaObj.currentVersion.functionArn,
        __get_project_data_files_lambda_function_arn__:
          getPieriandxDataFilesPyLambdaObj.currentVersion.functionArn,
        __get_sample_redcap_info_lambda_function_arn__:
          getDataFromRedCapPyLambdaObj.currentVersion.functionArn,

        /* Tables */
        __table_name__: props.tableObj.tableName,
        __library_table_partition_name__: this.PierianDxMap.tablePartition.library,

        /* Extras */
        __specimen_code__: this.PierianDxMap.defaultSpecimenCode,
        __specimen_label__: this.PierianDxMap.defaultSpecimenLabel,
      },
    });

    /*
    Part 2: Grant the sfn permissions
    */
    // access the dynamodb table
    props.tableObj.grantReadWriteData(inputMakerSfn);

    // allow the step function to invoke the lambdas
    [
      generatePortalRunIdPyLambdaObj,
      getDataFromRedCapPyLambdaObj,
      getDeidentifiedCaseMetadataPyLambdaObj,
      getIdentifiedCaseMetadataPyLambdaObj,
      getPieriandxDataFilesPyLambdaObj,
      getProjectInfoPyLambdaObj,
    ].forEach((lambdaObj) => {
      lambdaObj.currentVersion.grantInvoke(inputMakerSfn);
    });

    // Allow step function to submit events to the event bus
    props.eventBusObj.grantPutEventsTo(inputMakerSfn);

    /*
    Part 3: Subscribe to the event bus and trigger the internal sfn
    */
    const rule = new events.Rule(this, 'library_qc_complete_to_tn_draft', {
      ruleName: `stacky-${this.PierianDxMap.prefix}-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.PierianDxMap.triggerSource],
        detailType: [this.PierianDxMap.triggerDetailType],
        detail: {
          status: [{ 'equals-ignore-case': this.PierianDxMap.triggerStatus }],
          workflowName: [{ 'equals-ignore-case': this.PierianDxMap.triggerWorkflowName }],
        },
      },
    });

    // Add target of event to be the state machine
    rule.addTarget(
      new eventsTargets.SfnStateMachine(inputMakerSfn, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );
  }
}
