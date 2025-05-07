import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';
import path from 'path';
import { PythonUvFunction } from '../../../../../../../components/uv-python-lambda-image-builder';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as iam from 'aws-cdk-lib/aws-iam';
import {
  hostedZoneNameParameterPath,
  jwtSecretName,
} from '../../../../../../../../../config/constants';
import * as cdk from 'aws-cdk-lib';
import { NagSuppressions } from 'cdk-nag';
import { MetadataToolsPythonLambdaLayer } from '../../../../../../../components/python-metadata-tools-layer';
import { Duration } from 'aws-cdk-lib';

export interface NewSamplesheetEventShowerConstructProps {
  tableObj: dynamodb.ITableV2;
  eventBusObj: events.IEventBus;
}

export class NewSamplesheetEventShowerConstruct extends Construct {
  public readonly newSamplesheetEventShowerMap = {
    // General
    prefix: 'clag-new-ss-event-shower',
    // Tables
    tablePartition: {
      instrumentRun: 'instrument_run',
      subject: 'subject',
      library: 'library',
      project: 'project',
    },
    // Set event triggers
    triggerSource: 'orcabus.workflowmanager',
    triggerStatus: 'succeeded',
    triggerDetailType: 'WorkflowRunStateChange',
    triggerWorkflowName: 'bclconvert',
    // Set event outputs
    outputSource: 'orcabus.instrumentrunmanager',
    outputStatus: {
      startEventShower: 'SamplesheetRegisteredEventShowerStarting',
      completeEventShower: 'SamplesheetRegisteredEventShowerComplete',
      subjectInSamplesheet: 'SubjectInSamplesheet',
      libraryInSamplesheet: 'LibraryInSamplesheet',
      projectInSamplesheet: 'ProjectInSamplesheet',
    },
    outputDetailType: {
      showerTerminal: 'SamplesheetShowerStateChange',
      metadataInSampleSheet: 'SamplesheetMetadataUnion',
    },
    outputPayloadVersion: '0.1.0',
  };

  public readonly stateMachineObj: sfn.StateMachine;

  constructor(scope: Construct, id: string, props: NewSamplesheetEventShowerConstructProps) {
    super(scope, id);

    /*
    Part 0: Get tokens and ssm parameters
    */
    const jwtTokenSecretObj = secretsManager.Secret.fromSecretNameV2(
      this,
      'jwt_token_secret',
      jwtSecretName
    );

    const hostnameSsmParameterObj = ssm.StringParameter.fromStringParameterName(
      this,
      'hostname_ssm_parameter',
      hostedZoneNameParameterPath
    );

    /*
    Part 1: Build lambda layers
    */
    const metadataToolsLayer = new MetadataToolsPythonLambdaLayer(this, 'metadata-tools-layer', {
      layerPrefix: 'clag',
    }).lambdaLayerVersionObj;

    /*
    Part 1: Build lambdas
    */

    // Decompress samplesheet
    const getLibraryIdsFromGzippedSampleSheetLambdaFunction = new PythonUvFunction(
      this,
      'get_library_id_from_gzipped_samplesheet_lambda',
      {
        entry: path.join(__dirname, 'lambdas/get_library_ids_from_gzipped_samplesheet_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'get_library_ids_from_gzipped_samplesheet.py',
        handler: 'handler',
        memorySize: 2048,
      }
    );

    // Generate library event data
    const generateLibraryEventDataLambdaFunction = new PythonUvFunction(
      this,
      'generate_library_event_data_lambda',
      {
        entry: path.join(__dirname, 'lambdas/generate_library_event_data_objects_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'generate_library_event_data_objects.py',
        handler: 'handler',
        memorySize: 2048,
        environment: {
          /* SSM and Secrets Manager env vars */
          HOSTNAME_SSM_PARAMETER: hostnameSsmParameterObj.parameterName,
          ORCABUS_TOKEN_SECRET_ID: jwtTokenSecretObj.secretName,
        },
        timeout: Duration.seconds(60),
        layers: [metadataToolsLayer],
      }
    );

    // generateLibraryEventDataLambdaFunction needs permissions to read the secret and ssm parameter
    jwtTokenSecretObj.grantRead(generateLibraryEventDataLambdaFunction.currentVersion);
    hostnameSsmParameterObj.grantRead(generateLibraryEventDataLambdaFunction.currentVersion);

    /*
    Part 2: Build state machine
    */
    this.stateMachineObj = new sfn.StateMachine(this, 'update_database_on_new_samplesheet_sfn', {
      stateMachineName: `${this.newSamplesheetEventShowerMap.prefix}-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates',
          'samplesheet_event_shower_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* Standard event settings */
        __event_bus_name__: props.eventBusObj.eventBusName,
        __event_source__: this.newSamplesheetEventShowerMap.outputSource,

        /* Specific Event settings */
        // Start Event Shower
        __start_samplesheet_shower_detail_type__:
          this.newSamplesheetEventShowerMap.outputDetailType.showerTerminal,
        __start_samplesheet_shower_payload_version__:
          this.newSamplesheetEventShowerMap.outputPayloadVersion,
        __start_samplesheet_shower_status__:
          this.newSamplesheetEventShowerMap.outputStatus.startEventShower,

        // Library In Samplesheet
        __library_in_samplesheet_detail_type__:
          this.newSamplesheetEventShowerMap.outputDetailType.metadataInSampleSheet,
        __library_in_samplesheet_payload_version__:
          this.newSamplesheetEventShowerMap.outputPayloadVersion,
        __library_in_samplesheet_status__:
          this.newSamplesheetEventShowerMap.outputStatus.libraryInSamplesheet,

        // Complete Event Shower
        __complete_samplesheet_shower_detail_type__:
          this.newSamplesheetEventShowerMap.outputDetailType.showerTerminal,
        __complete_samplesheet_shower_payload_version__:
          this.newSamplesheetEventShowerMap.outputPayloadVersion,
        __complete_samplesheet_shower_status__:
          this.newSamplesheetEventShowerMap.outputStatus.completeEventShower,

        /* Table settings */
        __table_name__: props.tableObj.tableName,
        __library_table_partition_name__: this.newSamplesheetEventShowerMap.tablePartition.library,
        __instrument_run_table_partition_name__:
          this.newSamplesheetEventShowerMap.tablePartition.instrumentRun,

        // Lambdas
        __get_library_ids_from_gzipped_samplesheet_lambda_function_arn__:
          getLibraryIdsFromGzippedSampleSheetLambdaFunction.currentVersion.functionArn,
        __get_library_object_and_event_data_from_metadata_api_lambda_function_arn__:
          generateLibraryEventDataLambdaFunction.currentVersion.functionArn,
      },
    });

    /*
    Part 3: Wire up permissions
    */

    /* Allow state machine to write to the table */
    props.tableObj.grantReadWriteData(this.stateMachineObj);

    /* Allow state machine to invoke lambda */
    [
      getLibraryIdsFromGzippedSampleSheetLambdaFunction,
      generateLibraryEventDataLambdaFunction,
    ].forEach((lambda) => {
      lambda.currentVersion.grantInvoke(this.stateMachineObj);
    });

    /* Allow state machine to send events */
    props.eventBusObj.grantPutEventsTo(this.stateMachineObj);

    /* State machine runs a distributed map */
    // Because this steps execution uses a distributed map running an express step function, we
    // have to wire up some extra permissions
    // Grant the state machine's role to execute itself
    // However we cannot just grant permission to the role as this will result in a circular dependency
    // between the state machine and the role
    // Instead we use the workaround here - https://github.com/aws/aws-cdk/issues/28820#issuecomment-1936010520
    const distributedMapPolicy = new iam.Policy(this, 'sfn-distributed-map-policy', {
      document: new iam.PolicyDocument({
        statements: [
          new iam.PolicyStatement({
            resources: [this.stateMachineObj.stateMachineArn],
            actions: ['states:StartExecution'],
          }),
          new iam.PolicyStatement({
            resources: [
              `arn:aws:states:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:execution:${this.stateMachineObj.stateMachineName}/*:*`,
            ],
            actions: ['states:RedriveExecution'],
          }),
        ],
      }),
    });
    // Add the policy to the state machine role
    this.stateMachineObj.role.attachInlinePolicy(distributedMapPolicy);

    // Add in the nag suppressions
    NagSuppressions.addResourceSuppressions(
      [this.stateMachineObj, distributedMapPolicy],
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'statemachine needs wild card permissions on itself because of the distributed map nature of the state machine',
        },
      ],
      true
    );

    /*
    Part 4: Build event rule
    */
    const eventRule = new events.Rule(this, 'update_database_on_new_samplesheet_event_rule', {
      ruleName: `stacky-${this.newSamplesheetEventShowerMap.prefix}-event-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.newSamplesheetEventShowerMap.triggerSource],
        detailType: [this.newSamplesheetEventShowerMap.triggerDetailType],
        detail: {
          status: [{ 'equals-ignore-case': this.newSamplesheetEventShowerMap.triggerStatus }],
          workflowName: [
            {
              'equals-ignore-case': this.newSamplesheetEventShowerMap.triggerWorkflowName,
            },
          ],
        },
      },
    });

    // Add target to event rule
    eventRule.addTarget(
      new eventsTargets.SfnStateMachine(this.stateMachineObj, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );
  }
}
