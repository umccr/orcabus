/*

Quick 'glue' step

Which performs the following steps:

1. Listen to the bsshFastqCopy complete event
2. Read in the Instrument Run Id and the output uri
3. For every sample in the samplesheet, generate a fastq set for all fastqs for that sample
4. Generate an event saying that the fastq glue service has generated a bunch of fastq sets
  * This will be the trigger for downstream services to start building their analysis sets and
    running their requirements.
*/

import path from 'path';
import { Construct } from 'constructs';
import * as cdk from 'aws-cdk-lib';
import { Duration, Stack, StackProps } from 'aws-cdk-lib';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import { DefinitionBody, IStateMachine } from 'aws-cdk-lib/aws-stepfunctions';
import { Bucket } from 'aws-cdk-lib/aws-s3';
import { FastqToolsPythonLambdaLayer } from '../../../../components/python-fastq-tools-layer';
import { PythonUvFunction } from '../../../../components/uv-python-lambda-image-builder';
import * as events from 'aws-cdk-lib/aws-events';
import {
  BsshFastqCopyToAddReadSetCreationEventRuleProps,
  FastqGlueStackConfig,
  FastqSetGenerationTemplateFunctionProps,
  LambdaBuilderInputProps,
  LambdaNameList,
  lambdasBuilderInputProps,
  lambdaToRequirementsMapping,
  SequenceRunManagerToFastqSetCreationEventRuleProps,
} from './interfaces';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';
import { EventField, RuleTargetInput } from 'aws-cdk-lib/aws-events';
import * as iam from 'aws-cdk-lib/aws-iam';
import { NagSuppressions } from 'cdk-nag';
import { SequenceToolsPythonLambdaLayer } from '../../../../components/python-sequence-tools-layer';

// Some globals
export type FastqGlueStackProps = FastqGlueStackConfig & cdk.StackProps;

export class FastqGlueStack extends Stack {
  public readonly lambdaLayerPrefix: string = 'fqg'; // Data Sharing
  public lambdaObjects: { [key in LambdaNameList]: lambda.Function } = {} as {
    [key in LambdaNameList]: lambda.Function;
  };
  public readonly API_VERSION: string = 'v1';

  constructor(scope: Construct, id: string, props: StackProps & FastqGlueStackProps) {
    super(scope, id, props);

    // Get the bucket object
    const pipelineCacheBucket = Bucket.fromBucketName(
      this,
      'pipeline-cache-bucket-name',
      props.pipelineCacheBucketName
    );

    // Get the event bus as an object
    const eventBus = events.EventBus.fromEventBusName(this, 'eventBus', props.eventBusName);

    // Create the fastq tool layer
    const fastqLayer = new FastqToolsPythonLambdaLayer(this, 'fastq-tools-layer', {
      layerPrefix: this.lambdaLayerPrefix,
    }).lambdaLayerVersionObj;

    const sequenceLayer = new SequenceToolsPythonLambdaLayer(this, 'sequence-tools-layer', {
      layerPrefix: this.lambdaLayerPrefix,
    }).lambdaLayerVersionObj;

    /*
    Collect the required secret and ssm parameters for getting metadata
    */
    const hostnameSsmParameterObj = ssm.StringParameter.fromStringParameterName(
      this,
      'hostname_ssm_parameter',
      props.hostedZoneNameSsmParameterPath
    );
    const orcabusTokenSecretObj = secretsmanager.Secret.fromSecretNameV2(
      this,
      'orcabus_token_secret',
      props.orcabusTokenSecretsManagerPath
    );
    const metadataTrackingSheetIdSsmParameterObj =
      ssm.StringParameter.fromSecureStringParameterAttributes(
        this,
        'metadata_tracking_sheet_id_ssm_parameter',
        {
          parameterName: props.metadataTrackingSheetIdSsmParameterPath,
        }
      );
    const gDriveAuthJsonSsmParameterObj = ssm.StringParameter.fromSecureStringParameterAttributes(
      this,
      'gdrive_auth_json_ssm_parameter',
      {
        parameterName: props.gDriveAuthJsonSsmParameterPath,
      }
    );

    // Create the lambda functions
    this.createLambdaFunctions({
      layerRequirements: {
        hostnameSsmParameterObject: hostnameSsmParameterObj,
        orcabusTokenSecretObject: orcabusTokenSecretObj,
      },
      fastqToolsLayer: fastqLayer,
      sequenceToolsLayer: sequenceLayer,
      cacheBucketProps: {
        bucket: pipelineCacheBucket,
        prefix: props.pipelineCachePrefix,
      },
      // Few little hacks
      metadataTrackingSheetIdSsmParameterObject: metadataTrackingSheetIdSsmParameterObj,
      gDriveAuthJsonSsmParameterObject: gDriveAuthJsonSsmParameterObj,
    });

    // Create the state machine
    const fastqSetGenerationStateMachine = this.createFastqSetGenerationStateMachine({
      eventBus: eventBus,
      eventSource: props.eventSource,
      eventDetailType: props.eventDetailType,
    });

    // Create the add read set state machine
    const fastqAddReadSetStateMachine = this.createAddReadSetStateMachine();

    // Create the event rule to trigger the fastq set generation state machine
    this.createEventBridgeRuleToTriggerCreateFastqSetStateMachine({
      eventBus: eventBus,
      eventDetailType: props.sequenceRunStateChangeEventDetailType,
      eventSource: props.sequenceRunManageEventSource,
      eventStatus: 'SUCCEEDED',
      stateMachineTarget: fastqSetGenerationStateMachine,
    });

    // Create rule to trigger the add read set state machine
    this.createEventBridgeRuleToTriggerAddReadSetStateMachine({
      eventBus: eventBus,
      eventDetailType: props.workflowRunStateChangeEventDetailType,
      eventSource: props.workflowManagerEventSource,
      eventStatus: 'SUCCEEDED',
      eventWorkflowName: props.bsshFastqCopyManagerWorkflowName,
      stateMachineTarget: fastqAddReadSetStateMachine,
    });
  }

  private camelCaseToSnakeCase(camelCase: string): string {
    return camelCase.replace(/([A-Z])/g, '_$1').toLowerCase();
  }

  private createFastqSetGenerationStateMachine(
    props: FastqSetGenerationTemplateFunctionProps
  ): IStateMachine {
    // Create the aws step function
    const fastqSetGenerationStateMachine = new sfn.StateMachine(this, 'fastqSetGenerationSfn', {
      // State Machine Name
      stateMachineName: 'fastq-glue-fastq-set-generation-sfn',
      // Definition
      definitionBody: DefinitionBody.fromFile(
        path.join(
          __dirname,
          '../step_functions_templates/fastq_set_generation_template_sfn.asl.json'
        )
      ),
      // Definition Substitutions
      definitionSubstitutions: {
        __event_bus_name__: props.eventBus.eventBusName,
        __event_source__: props.eventSource,
        __event_detail_type__: props.eventDetailType,
        // All lambda substitutions
        ...this.createLambdaDefinitionSubstitutions(),
      },
    });

    // For all lambdas in the props.lambdaObjects, grant invoke permissions to the state machine
    let lambdaName: LambdaNameList;
    for (lambdaName in this.lambdaObjects) {
      this.lambdaObjects[lambdaName].currentVersion.grantInvoke(fastqSetGenerationStateMachine);
    }

    // Grant permissions for the state machine to write to the event bus
    props.eventBus.grantPutEventsTo(fastqSetGenerationStateMachine);

    // Because this steps execution uses a distributed map running an express step function, we
    // have to wire up some extra permissions
    // Grant the state machine's role to execute itself
    // However we cannot just grant permission to the role as this will result in a circular dependency
    // between the state machine and the role
    // Instead we use the workaround here - https://github.com/aws/aws-cdk/issues/28820#issuecomment-1936010520
    // fastqSetGenerationStateMachine.grantStartExecution(fastqSetGenerationStateMachine.role);
    const distributedMapPolicy = new iam.Policy(this, 'fastq-set-sfn-distributed-map-policy', {
      document: new iam.PolicyDocument({
        statements: [
          new iam.PolicyStatement({
            resources: [fastqSetGenerationStateMachine.stateMachineArn],
            actions: ['states:StartExecution'],
          }),
          new iam.PolicyStatement({
            resources: [
              `arn:aws:states:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:execution:${fastqSetGenerationStateMachine.stateMachineName}/*:*`,
            ],
            actions: ['states:RedriveExecution'],
          }),
        ],
      }),
    });

    // Add the policy to the state machine role
    fastqSetGenerationStateMachine.role.attachInlinePolicy(distributedMapPolicy);

    // Treat the state machine as if it's running a nested statemachine
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    fastqSetGenerationStateMachine.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );

    // Redrive execution requires permissions to list state machine executions
    NagSuppressions.addResourceSuppressions(
      [fastqSetGenerationStateMachine, distributedMapPolicy],
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'grantRead uses asterisk at the end of executions, as we need permissions for all execution invocations',
        },
      ],
      true
    );

    return fastqSetGenerationStateMachine;
  }

  private createAddReadSetStateMachine(): IStateMachine {
    // Create the aws step function
    const fastqAddReadSetStateMachine = new sfn.StateMachine(this, 'AddReadSetGeneration', {
      // State Machine Name
      stateMachineName: 'fastq-glue-add-read-set-sfn',
      // Definition
      definitionBody: DefinitionBody.fromFile(
        path.join(
          __dirname,
          '../step_functions_templates/fastq_set_add_read_set_template_sfn.asl.json'
        )
      ),
      // Definition Substitutions
      definitionSubstitutions: {
        // All lambda substitutions
        ...this.createLambdaDefinitionSubstitutions(),
      },
    });

    // For all lambdas in the props.lambdaObjects, grant invoke permissions to the state machine
    let lambdaName: LambdaNameList;
    for (lambdaName in this.lambdaObjects) {
      this.lambdaObjects[lambdaName].currentVersion.grantInvoke(fastqAddReadSetStateMachine);
    }

    // Because this steps execution uses a distributed map running an express step function, we
    // have to wire up some extra permissions
    // Grant the state machine's role to execute itself
    // However we cannot just grant permission to the role as this will result in a circular dependency
    // between the state machine and the role
    // Instead we use the workaround here - https://github.com/aws/aws-cdk/issues/28820#issuecomment-1936010520
    // fastqAddReadSetStateMachine.grantStartExecution(fastqAddReadSetStateMachine.role);
    const distributedMapPolicy = new iam.Policy(
      this,
      'fastq-add-read-set-sfn-distributed-map-policy',
      {
        document: new iam.PolicyDocument({
          statements: [
            new iam.PolicyStatement({
              resources: [fastqAddReadSetStateMachine.stateMachineArn],
              actions: ['states:StartExecution'],
            }),
            new iam.PolicyStatement({
              resources: [
                `arn:aws:states:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:execution:${fastqAddReadSetStateMachine.stateMachineName}/*:*`,
              ],
              actions: ['states:RedriveExecution'],
            }),
          ],
        }),
      }
    );

    // Add the policy to the state machine role
    fastqAddReadSetStateMachine.role.attachInlinePolicy(distributedMapPolicy);

    // Treat the state machine as if it's running a nested statemachine
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    fastqAddReadSetStateMachine.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );

    // Redrive execution requires permissions to list state machine executions
    NagSuppressions.addResourceSuppressions(
      [fastqAddReadSetStateMachine, distributedMapPolicy],
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'grantRead uses asterisk at the end of executions, as we need permissions for all execution invocations',
        },
      ],
      true
    );

    return fastqAddReadSetStateMachine;
  }

  private createLambdaFunction(props: LambdaBuilderInputProps): PythonFunction {
    const lambdaNameToSnakeCase = this.camelCaseToSnakeCase(props.lambdaName);

    // Initialise layer list
    const layers = [];

    // Add the fastq tools layer if it is required
    if (props.fastqToolsLayer) {
      layers.push(props.fastqToolsLayer);
    }
    if (props.sequenceToolsLayer) {
      layers.push(props.sequenceToolsLayer);
    }

    // Create the lambda function
    const lambdaFunction = new PythonUvFunction(this, props.lambdaName, {
      entry: path.join(__dirname, '../lambdas', lambdaNameToSnakeCase + '_py'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: lambdaNameToSnakeCase + '.py',
      handler: 'handler',
      timeout: Duration.seconds(60),
      memorySize: 2048,
      layers: layers,
    });

    // Add envs / permissions to the lambda function
    if (props.layerRequirements) {
      lambdaFunction.addEnvironment(
        /* SSM and Secrets Manager env vars */
        'HOSTNAME_SSM_PARAMETER',
        props.layerRequirements.hostnameSsmParameterObject.parameterName
      );
      lambdaFunction.addEnvironment(
        'ORCABUS_TOKEN_SECRET_ID',
        props.layerRequirements.orcabusTokenSecretObject.secretName
      );

      // Add permissions to the lambda function
      props.layerRequirements.hostnameSsmParameterObject.grantRead(lambdaFunction.currentVersion);
      props.layerRequirements.orcabusTokenSecretObject.grantRead(lambdaFunction.currentVersion);
    }

    if (props.cacheBucketProps) {
      props.cacheBucketProps.bucket.grantRead(
        lambdaFunction.currentVersion,
        `${props.cacheBucketProps.prefix}*`
      );

      // Add the cdk nag
      NagSuppressions.addResourceSuppressions(
        lambdaFunction,
        [
          {
            id: 'AwsSolutions-IAM5',
            reason: 'Added permissions to the lambda function to read from the cache bucket',
          },
        ],
        true
      );
    }

    return lambdaFunction;
  }

  private createLambdaFunctions(props: lambdasBuilderInputProps) {
    // Iterate over lambdaLayerToMapping and create the lambda functions
    let lambdaName: LambdaNameList;
    for (lambdaName in lambdaToRequirementsMapping) {
      this.lambdaObjects[lambdaName] = this.createLambdaFunction({
        lambdaName: lambdaName,
        ...{
          layerRequirements: lambdaToRequirementsMapping[lambdaName].needsFastqToolsLayer
            ? props.layerRequirements
            : undefined,
          fastqToolsLayer: lambdaToRequirementsMapping[lambdaName].needsFastqToolsLayer
            ? props.fastqToolsLayer
            : undefined,
          sequenceToolsLayer: lambdaToRequirementsMapping[lambdaName].needsSequenceToolsLayer
            ? props.sequenceToolsLayer
            : undefined,
          cacheBucketProps: lambdaToRequirementsMapping[lambdaName].needsCacheBucketReadPermissions
            ? props.cacheBucketProps
            : undefined,
        },
      });

      if (lambdaName == 'createFastqSetObject') {
        this.lambdaObjects[lambdaName].addEnvironment(
          'METADATA_TRACKING_SHEET_ID_SSM_PARAMETER_PATH',
          props.metadataTrackingSheetIdSsmParameterObject.parameterName
        );
        this.lambdaObjects[lambdaName].addEnvironment(
          'GDRIVE_AUTH_JSON_SSM_PARAMETER_PATH',
          props.gDriveAuthJsonSsmParameterObject.parameterName
        );
        // Add permissions to the lambda function
        props.metadataTrackingSheetIdSsmParameterObject.grantRead(
          this.lambdaObjects[lambdaName].currentVersion
        );
        props.gDriveAuthJsonSsmParameterObject.grantRead(
          this.lambdaObjects[lambdaName].currentVersion
        );
      }
    }
  }

  private createLambdaDefinitionSubstitutions(): { [key: string]: string } {
    const definitionSubstitutions: { [key: string]: string } = {};

    let lambdaName: LambdaNameList;
    for (lambdaName in this.lambdaObjects) {
      const lambdaObject = this.lambdaObjects[lambdaName];
      const sfnSubtitutionKey = `__${this.camelCaseToSnakeCase(lambdaName)}_lambda_function_arn__`;
      definitionSubstitutions[sfnSubtitutionKey] = lambdaObject.currentVersion.functionArn;
    }
    return definitionSubstitutions;
  }

  private createEventBridgeRuleToTriggerCreateFastqSetStateMachine(
    props: SequenceRunManagerToFastqSetCreationEventRuleProps
  ): events.Rule {
    /*
    Listen to the sequence run manager events and then trigger the fastq set state machine
    */
    const eventRule = new events.Rule(this, 'sequenceRunManagerEventSucceeded', {
      ruleName: `fastq-glue-sequence-run-manager-event-succeeded`,
      eventBus: props.eventBus,
      eventPattern: {
        source: [props.eventSource],
        detailType: [props.eventDetailType],
        detail: {
          status: [{ 'equals-ignore-case': props.eventStatus }],
        },
      },
    });

    // Add target to event rule
    // Note that we expect fastqListRowIdList as our only input
    // While the fastqUnarchivingComplete event detail body contains the fastq list row objects we need to
    // rename the list to match the input requirements of the step function
    eventRule.addTarget(
      new eventsTargets.SfnStateMachine(props.stateMachineTarget, {
        input: RuleTargetInput.fromObject({
          instrumentRunId: EventField.fromPath('$.detail.instrumentRunId'),
        }),
      })
    );

    return eventRule;
  }

  private createEventBridgeRuleToTriggerAddReadSetStateMachine(
    props: BsshFastqCopyToAddReadSetCreationEventRuleProps
  ): events.Rule {
    /*
    Listen to the bssh fastq copy events and then trigger the fastq add read-set state machine
    */
    const eventRule = new events.Rule(this, 'bsshFastqCopySucceeded', {
      ruleName: `fastq-glue-bssh-fastq-copy-succeeded`,
      eventBus: props.eventBus,
      eventPattern: {
        source: [props.eventSource],
        detailType: [props.eventDetailType],
        detail: {
          status: [{ 'equals-ignore-case': props.eventStatus }],
          workflowName: [{ 'equals-ignore-case': props.eventWorkflowName }],
        },
      },
    });

    // Add target to event rule
    // Note that we expect fastqListRowIdList as our only input
    // While the fastqUnarchivingComplete event detail body contains the fastq list row objects we need to
    // rename the list to match the input requirements of the step function
    eventRule.addTarget(
      new eventsTargets.SfnStateMachine(props.stateMachineTarget, {
        input: RuleTargetInput.fromObject({
          instrumentRunId: EventField.fromPath('$.detail.payload.data.outputs.instrumentRunId'),
          outputUri: EventField.fromPath('$.detail.payload.data.outputs.outputUri'),
        }),
      })
    );

    return eventRule;
  }
}
