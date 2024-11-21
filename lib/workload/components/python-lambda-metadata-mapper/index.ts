/*
Quick and dirty way to map orcabus ids to complementary ids for each
of the databases from the metadata manager

Comes with the bells and whistles of metadata tools layer and
permissions to use the orcabus token.

User will need to use the 'addEnvironment' method on the returned lambda object in order
to specify what command will be run

User will need

ENV:
CONTEXT: One of the following:
  - library
  - subject
  - individual
  - sample
  - project
  - contact

FROM_ORCABUS or FROM_ID
RETURN_STR or RETURN_OBJ

Look at ./map_metadata_py/map_metadata.py for examples of outputs

*/

import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import path from 'path';
import { MetadataToolsPythonLambdaLayer } from '../python-metadata-tools-layer';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { Duration } from 'aws-cdk-lib';

interface MapMetadataLambdaObj {
  functionNamePrefix: string;
}

export class GetMetadataLambdaConstruct extends Construct {
  public readonly lambdaObj: PythonFunction;

  // Globals
  private readonly hostnameSsmParameterPath = '/hosted_zone/umccr/name';
  private readonly orcabusTokenSecretId = 'orcabus/token-service-jwt'; // pragma: allowlist secret

  constructor(scope: Construct, id: string, props: MapMetadataLambdaObj) {
    super(scope, id);

    // Get the metadata layer object
    const metadataLayerObj = new MetadataToolsPythonLambdaLayer(this, 'metadata-tools-layer', {
      layerPrefix: `${props.functionNamePrefix}-mtl`,
    });

    /*
    Collect the required secret and ssm parameters for getting metadata
    */
    const hostnameSsmParameterObj = ssm.StringParameter.fromStringParameterName(
      this,
      'hostname_ssm_parameter',
      this.hostnameSsmParameterPath
    );
    const orcabusTokenSecretObj = secretsmanager.Secret.fromSecretNameV2(
      this,
      'orcabus_token_secret',
      this.orcabusTokenSecretId
    );

    // Get library objects
    this.lambdaObj = new PythonFunction(this, 'map_metadata_py', {
      functionName: `${props.functionNamePrefix}-map-metadata-py`,
      entry: path.join(__dirname, 'map_metadata_py'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'map_metadata.py',
      handler: 'handler',
      memorySize: 1024,
      layers: [metadataLayerObj.lambdaLayerVersionObj],
      environment: {
        HOSTNAME_SSM_PARAMETER: hostnameSsmParameterObj.parameterName,
        ORCABUS_TOKEN_SECRET_ID: orcabusTokenSecretObj.secretName,
      },
      timeout: Duration.seconds(60),
    });

    // Allow the lambda to read the secret
    orcabusTokenSecretObj.grantRead(this.lambdaObj.currentVersion);

    // Allow the lambda to read the ssm parameter
    hostnameSsmParameterObj.grantRead(this.lambdaObj.currentVersion);
  }
}
