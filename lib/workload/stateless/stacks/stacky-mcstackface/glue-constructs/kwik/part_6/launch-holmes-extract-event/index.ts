import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import path from 'path';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';
import { LambdaServiceDiscoveryConstruct } from '../../../../../../../components/python-lambda-service-discovery';
import { LambdaDiscoverInstancesConstruct } from '../../../../../../../components/python-lambda-list-service-instances';
import { GetMetadataLambdaConstruct } from '../../../../../../../components/python-lambda-metadata-mapper';
import { GetWorkflowPayloadLambdaConstruct } from '../../../../../../../components/python-lambda-get-workflow-payload';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as cdk from 'aws-cdk-lib';
import { NagSuppressions } from 'cdk-nag';

/*
Part 7

Input Event Source: `orcabus.wgtsqcinputeventglue`
Input Event DetailType: `LibraryStateChange`
Input Event status: `QC_COMPLETE`

Output Event Source: `orcabus.wgtsqcinputeventglue`
Output Event DetailType: `LibraryStateChange`
Output Event status: `HOLMES_EXTRACTION_COMPLETE`

* Once all fastq list rows have been processed for a given library, we fire off a library state change event
* This will contain the qc information such as coverage + duplicate rate (for wgs) or exon coverage (for wts)

*/

export interface HolmesExtractConstructProps {
  tableObj: dynamodb.ITableV2;
  eventBusObj: events.IEventBus;
}

export class HolmesExtractConstruct extends Construct {
  public readonly HolmesExtractMap = {
    prefix: 'kwik-holmes-extract-complete',
    payloadVersion: '2024.07.16',
    triggerSource: 'orcabus.wgtsqcinputeventglue',
    triggerStatus: 'QC_COMPLETE',
    triggerDetailType: 'LibraryStateChange',
    outputSource: 'orcabus.wgtsqcinputeventglue',
    outputDetailType: 'LibraryStateChange',
    outputStatus: 'HOLMES_EXTRACTION_COMPLETE',
    serviceName: 'fingerprint',
    extractStepsArnKey: 'extractStepsArn',
    referenceName: 'hg38.rna',
    tablePartitions: {
      fastqListRow: 'fastq_list_row',
      library: 'library',
    },
    /*
    FIXME - cloudmap paradox
      we cannot find the cloudmap service inside cdk
      but we need to give the parent step function permission
      to invoke the child step function
      so in the meantime just hardcode the arn prefix
      and set a cdk nag suppression
     */
    extractStepsArnPrefix: 'SomalierExtractStateMachine',
  };

  constructor(scope: Construct, id: string, props: HolmesExtractConstructProps) {
    super(scope, id);

    /*
    Part 1a: Lambdas for collecting the cloud-map services
    */
    const serviceDiscoveryLambdaObj = new LambdaServiceDiscoveryConstruct(
      this,
      'service_discovery_lambda',
      {
        functionNamePrefix: this.HolmesExtractMap.prefix,
      }
    ).lambdaObj;

    const serviceListInstancesLambdaObj = new LambdaDiscoverInstancesConstruct(
      this,
      'service_list_instances_lambda',
      {
        functionNamePrefix: this.HolmesExtractMap.prefix,
      }
    ).lambdaObj;

    /*
    Part 1b: Lambdas for getting the library object from the library id
    */
    // Generate the lambda to collect the orcabus id from the subject id
    const collectLibraryObjLambdaObj = new GetMetadataLambdaConstruct(
      this,
      'get_library_obj_from_library_id_lambda',
      {
        functionNamePrefix: `${this.HolmesExtractMap.prefix}-lib`,
      }
    ).lambdaObj;

    // Add CONTEXT, FROM_ID and RETURN_OBJ environment variables to the lambda
    collectLibraryObjLambdaObj.addEnvironment('CONTEXT', 'library');
    collectLibraryObjLambdaObj.addEnvironment('FROM_ORCABUS', '');
    collectLibraryObjLambdaObj.addEnvironment('RETURN_OBJ', '');

    const collectIndividualObjLambdaObj = new GetMetadataLambdaConstruct(
      this,
      'get_individual_obj_from_subject_lambda',
      {
        functionNamePrefix: `${this.HolmesExtractMap.prefix}-idv`,
      }
    ).lambdaObj;
    // Add CONTEXT, FROM_ID and RETURN_OBJ environment variables to the lambda
    collectIndividualObjLambdaObj.addEnvironment('CONTEXT', 'subject');
    collectIndividualObjLambdaObj.addEnvironment('FROM_ORCABUS', '');
    collectIndividualObjLambdaObj.addEnvironment('RETURN_OBJ', '');

    /*
    Part 1c: Get the alignment bam uri from the portal run id
    Requires the workflow lambda layer and the orcabus token
    */
    const getWorkflowPayloadLambdaObj = new GetWorkflowPayloadLambdaConstruct(
      this,
      'get_workflow_payload_lambda',
      {
        functionNamePrefix: this.HolmesExtractMap.prefix,
      }
    ).lambdaObj;

    /*
    Part 1: Build the sfn
    */
    const holmesWrapperSfn = new sfn.StateMachine(this, 'holmes_wrapper_sfn', {
      stateMachineName: `${this.HolmesExtractMap.prefix}-wrapper-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates',
          'holmes_extract_wrapper_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* Event stuff */
        __event_bus_name__: props.eventBusObj.eventBusName,
        __event_source__: this.HolmesExtractMap.outputSource,
        __detail_type__: this.HolmesExtractMap.outputDetailType,
        __payload_version__: this.HolmesExtractMap.payloadVersion,
        __status__: this.HolmesExtractMap.outputStatus,
        /* Table stuff */
        __table_name__: props.tableObj.tableName,
        __fastq_list_row_table_partition_name__: this.HolmesExtractMap.tablePartitions.fastqListRow,
        __library_table_partition_name__: this.HolmesExtractMap.tablePartitions.library,
        /* Cloud Map Stuff */
        __service_name__: this.HolmesExtractMap.serviceName,
        __extract_arn_key__: this.HolmesExtractMap.extractStepsArnKey,
        /* Lambdas */
        __get_cloudmap_service_lambda_function_arn__:
          serviceDiscoveryLambdaObj.currentVersion.functionArn,
        __get_service_instances_lambda_function_arn__:
          serviceListInstancesLambdaObj.currentVersion.functionArn,
        __get_library_obj_lambda_function_arn__:
          collectLibraryObjLambdaObj.currentVersion.functionArn,
        __get_alignment_bam_uri_lambda_function_arn__:
          getWorkflowPayloadLambdaObj.currentVersion.functionArn,
        __get_individual_obj_lambda_function_arn__:
          collectIndividualObjLambdaObj.currentVersion.functionArn,
        /* Reference input */
        __reference_name__: this.HolmesExtractMap.referenceName,
      },
    });

    /*
    Part 2: Grant the internal sfn permissions
    */
    // access the dynamodb table
    props.tableObj.grantReadWriteData(holmesWrapperSfn.role);
    // invoke the lambda function
    [
      serviceDiscoveryLambdaObj,
      serviceListInstancesLambdaObj,
      collectLibraryObjLambdaObj,
      getWorkflowPayloadLambdaObj,
      collectIndividualObjLambdaObj,
    ].forEach((lambdaObj) => {
      lambdaObj.currentVersion.grantInvoke(holmesWrapperSfn);
    });

    // Push events to the event bus
    props.eventBusObj.grantPutEventsTo(holmesWrapperSfn.role);

    // Because we run a nested state machine, we need to add the permissions to the state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    holmesWrapperSfn.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );

    // Add permissions to the statemachine to allow execution of the holmes extract state machine
    holmesWrapperSfn.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:states:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:stateMachine:${this.HolmesExtractMap.extractStepsArnPrefix}*`,
        ],
        actions: ['states:StartExecution'],
      })
    );

    // Add cdk nag suppressions
    // FIXME - cannot get the full arn of the extractStepsArn in CDK
    NagSuppressions.addResourceSuppressions(
      holmesWrapperSfn,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason: 'Cannot get the extractStepsArn full path in CDK',
        },
      ],
      true
    );

    /*
    Part 3: Subscribe to the event bus and trigger the internal sfn
    */
    const rule = new events.Rule(this, 'wgts_subscribe_to_library_qc_complete', {
      ruleName: `stacky-${this.HolmesExtractMap.prefix}-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.HolmesExtractMap.triggerSource],
        detailType: [this.HolmesExtractMap.triggerDetailType],
        detail: {
          status: [{ 'equals-ignore-case': this.HolmesExtractMap.triggerStatus }],
        },
      },
    });

    // Add target of event to be the state machine
    rule.addTarget(
      new eventsTargets.SfnStateMachine(holmesWrapperSfn, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );
  }
}
