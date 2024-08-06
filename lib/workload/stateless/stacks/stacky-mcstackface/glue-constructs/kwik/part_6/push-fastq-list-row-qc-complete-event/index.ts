import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import path from 'path';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Duration } from 'aws-cdk-lib';

/*
Part 6

Input Event Source: `orcabus.workflowmanager`
Input Event DetailType: `WorkflowRunStateChange`
Input Event status: `succeeded`
Input Event WorkflowName: `wgts_qc`

Output Event Source: `orcabus.wgtsqcinputeventglue`
Output Event DetailType: `FastqListRowStateChange`
Output Event status: `QcComplete`

* Subscribe to workflow run state change events, map the fastq list row id from the portal run id in the database
* We output the fastq list row id to the event bus with the status `QcComplete`
*/

export interface FastqListRowQcCompleteConstructProps {
  eventBusObj: events.IEventBus;
  tableObj: dynamodb.ITableV2;
  icav2JwtSecretsObj: secretsManager.ISecret;
}

export class FastqListRowQcCompleteConstruct extends Construct {
  public readonly WgtsQcCompleteMap = {
    prefix: 'kwik-fqlr-qc-complete',
    tablePartition: 'fastq_list_row',
    portalRunPartitionName: 'portal_run',
    triggerSource: 'orcabus.workflowmanager',
    triggerStatus: 'succeeded',
    triggerDetailType: 'WorkflowRunStateChange',
    triggerWorkflowName: 'wgtsQc',
    outputSource: 'orcabus.wgtsqcinputeventglue',
    outputDetailType: 'FastqListRowStateChange',
    outputStatus: 'QcComplete',
    payloadVersion: '2024.05.24',
  };

  constructor(scope: Construct, id: string, props: FastqListRowQcCompleteConstructProps) {
    super(scope, id);

    /*
    Part 1: Build the lambdas
    */
    const collectMetricsLambdaObj = new PythonFunction(
      this,
      'collect_qc_metrics_from_alignment_directory_py',
      {
        entry: path.join(__dirname, 'lambdas', 'collect_qc_metrics_from_alignment_directory_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'collect_qc_metrics_from_alignment_directory.py',
        handler: 'handler',
        memorySize: 1024,
        environment: {
          ICAV2_ACCESS_TOKEN_SECRET_ID: props.icav2JwtSecretsObj.secretName,
        },
        timeout: Duration.seconds(30),
      }
    );

    // Allow the lambdas to access the icav2JwtSecretsObj
    props.icav2JwtSecretsObj.grantRead(<iam.IRole>collectMetricsLambdaObj.role);

    // Generate event data lambda object
    const generateEventDataLambdaObj = new PythonFunction(this, 'generate_event_data_objects_py', {
      entry: path.join(__dirname, 'lambdas', 'generate_event_data_objects_py'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'generate_event_data_objects.py',
      handler: 'handler',
      memorySize: 1024,
    });

    /*
    Part 2: Build the sfn
    */
    const qcCompleteSfn = new sfn.StateMachine(this, 'qc_complete_sfn', {
      stateMachineName: `${this.WgtsQcCompleteMap.prefix}-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(__dirname, 'step_functions_templates', 'wgts_qc_complete_sfn_template.asl.json')
      ),
      definitionSubstitutions: {
        /* Events */
        __event_bus_name__: props.eventBusObj.eventBusName,
        __event_source__: this.WgtsQcCompleteMap.outputSource,
        __detail_type__: this.WgtsQcCompleteMap.outputDetailType,
        __output_status__: this.WgtsQcCompleteMap.outputStatus,
        __payload_version__: this.WgtsQcCompleteMap.payloadVersion,

        /* Lambdas */
        __generate_event_output_objects_lambda_function_arn__:
          generateEventDataLambdaObj.currentVersion.functionArn,
        __collect_qc_metrics_lambda_function_arn__:
          collectMetricsLambdaObj.currentVersion.functionArn,

        /* Tables */
        __table_name__: props.tableObj.tableName,
        __fastq_list_row_partition__: this.WgtsQcCompleteMap.tablePartition,
        __portal_run_partition_name__: 'portal_run',
        __library_partition__: 'library',
      },
    });

    /*
    Part 2: Grant the sfn permissions
    */
    // access the dynamodb table
    props.tableObj.grantReadWriteData(qcCompleteSfn.role);

    // allow the step function to submit events
    props.eventBusObj.grantPutEventsTo(qcCompleteSfn.role);

    // allow the step function to invoke the lambdas
    [generateEventDataLambdaObj, collectMetricsLambdaObj].forEach((lambdaObj) => {
      lambdaObj.currentVersion.grantInvoke(qcCompleteSfn.role);
    });

    /*
    Part 3: Subscribe to the event bus and trigger the internal sfn
    */
    const rule = new events.Rule(this, 'wgts_subscribe_to_samplesheet_shower', {
      ruleName: `stacky-${this.WgtsQcCompleteMap.prefix}-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.WgtsQcCompleteMap.triggerSource],
        detailType: [this.WgtsQcCompleteMap.triggerDetailType],
        detail: {
          status: [{ 'equals-ignore-case': this.WgtsQcCompleteMap.triggerStatus }],
          workflowName: [
            {
              'equals-ignore-case': this.WgtsQcCompleteMap.triggerWorkflowName,
            },
          ],
        },
      },
    });

    // Add target of event to be the state machine
    rule.addTarget(
      new eventsTargets.SfnStateMachine(qcCompleteSfn, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );
  }
}
