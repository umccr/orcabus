/*

Populate the library database for an instrument run

We need to collect the following attributes in the library database for each sample in pieriandx:

subject_id
project_name
project_owner
instrument_run_id
external_subject_id
external_sample_id

We store this under the library table

*/

import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import path from 'path';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { MetadataToolsPythonLambdaLayer } from '../../../../../../../components/python-metadata-tools-layer';
import {
  hostedZoneNameParameterPath,
  jwtSecretName,
} from '../../../../../../../../../config/constants';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { Duration } from 'aws-cdk-lib';

export interface PieriandxInitialiseLibraryConstructProps {
  tableObj: dynamodb.ITableV2;
  eventBusObj: events.IEventBus;
}

export class PieriandxInitialiseLibraryConstruct extends Construct {
  public readonly PieriandxInitialiseLibrary = {
    prefix: 'nails-make-library',
    tablePartition: {
      library: 'library',
    },
    triggerSource: 'orcabus.fastqglue',
    triggerStatus: 'LibraryInSamplesheet',
    triggerDetailType: 'SamplesheetMetadataUnion',
    triggerAssayType: {
      v1: 'cttso',
      v2: 'cttsov2',
    },
  };

  constructor(scope: Construct, id: string, props: PieriandxInitialiseLibraryConstructProps) {
    super(scope, id);

    /*
    Part 0: Get the metadata layer
   */
    // Get the metadata layer object
    const metadataLayerObj = new MetadataToolsPythonLambdaLayer(this, 'metadata-tools-layer', {
      layerPrefix: 'nails-get-library',
    });

    /*
    Collect the required secret and ssm parameters for getting metadata
    */
    const hostnameSsmParameterObj = ssm.StringParameter.fromStringParameterName(
      this,
      'hostname_ssm_parameter',
      hostedZoneNameParameterPath
    );
    const orcabusTokenSecretObj = secretsmanager.Secret.fromSecretNameV2(
      this,
      'orcabus_token_secret',
      jwtSecretName
    );

    // Get library objects
    const lambdaObj = new PythonFunction(this, 'get_project_id_from_library_id_py', {
      entry: path.join(__dirname, 'lambdas', 'get_project_id_from_library_id_py'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'get_project_id_from_library_id.py',
      handler: 'handler',
      memorySize: 1024,
      layers: [metadataLayerObj.lambdaLayerVersionObj],
      environment: {
        HOSTNAME_SSM_PARAMETER: hostnameSsmParameterObj.parameterName,
        ORCABUS_TOKEN_SECRET_ID: orcabusTokenSecretObj.secretName,
      },
      // We dont know how big the database will get so will may need a longer timeout
      timeout: Duration.seconds(120),
    });

    // Allow the lambda to read the secret
    orcabusTokenSecretObj.grantRead(lambdaObj.currentVersion);

    // Allow the lambda to read the ssm parameter
    hostnameSsmParameterObj.grantRead(lambdaObj.currentVersion);

    /*
    Part 1: Build the internal sfn
    */
    const inputMakerSfn = new sfn.StateMachine(this, 'initialise_pieriandx_library_db_row', {
      stateMachineName: `${this.PieriandxInitialiseLibrary.prefix}-initialise-pieriandx-library-db`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates',
          'store_cttsov2_metadata_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* General */
        __table_name__: props.tableObj.tableName,

        /* Lambdas */
        __get_project_id_from_library_id_lambda_function_arn__:
          lambdaObj.currentVersion.functionArn,

        /* Table Partitions */
        __library_partition_name__: this.PieriandxInitialiseLibrary.tablePartition.library,
      },
    });

    /*
    Part 2: Grant the sfn permissions
    */
    // access the dynamodb table
    props.tableObj.grantReadWriteData(inputMakerSfn);
    // invoke the lambda
    lambdaObj.currentVersion.grantInvoke(inputMakerSfn);

    /*
    Part 3: Subscribe to the library events from the event bus where the library assay type
    is WGS and the workflow is RESEARCH or CLINICAL
    and where the phenotype is NORMAL or TUMOR
    */
    const rule = new events.Rule(this, 'initialise_library_assay', {
      ruleName: `stacky-${this.PieriandxInitialiseLibrary.prefix}-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.PieriandxInitialiseLibrary.triggerSource],
        detailType: [this.PieriandxInitialiseLibrary.triggerDetailType],
        detail: {
          payload: {
            data: {
              library: {
                assay: [
                  {
                    'equals-ignore-case': this.PieriandxInitialiseLibrary.triggerAssayType.v1,
                  },
                  {
                    'equals-ignore-case': this.PieriandxInitialiseLibrary.triggerAssayType.v2,
                  },
                ],
              },
            },
          },
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
