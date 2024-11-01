import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import path from 'path';
import { MetadataToolsPythonLambdaLayer } from '../python-metadata-tools-layer';
import { Duration } from 'aws-cdk-lib';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';

interface GetLibraryObjectsFromSamplesheetProps {
  functionNamePrefix: string;
}

export class GetLibraryObjectsFromSamplesheetConstruct extends Construct {
  public readonly lambdaObj: PythonFunction;

  // Globals
  private readonly hostnameSsmParameterPath = '/hosted_zone/umccr/name';
  private readonly orcabusTokenSecretId = 'orcabus/token-service-jwt'; // pragma: allowlist secret

  constructor(scope: Construct, id: string, props: GetLibraryObjectsFromSamplesheetProps) {
    super(scope, id);

    // Get the metadata layer object
    const metadataLayerObj = new MetadataToolsPythonLambdaLayer(this, 'metadata-tools-layer', {
      layerPrefix: 'get-library-objects',
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
    this.lambdaObj = new PythonFunction(this, 'get_library_objects_from_samplesheet', {
      functionName: `${props.functionNamePrefix}-library-objs-from-ss`,
      entry: path.join(__dirname, 'get_metadata_objects_from_samplesheet_py'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'get_metadata_objects_from_samplesheet.py',
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
    orcabusTokenSecretObj.grantRead(this.lambdaObj.currentVersion);

    // Allow the lambda to read the ssm parameter
    hostnameSsmParameterObj.grantRead(this.lambdaObj.currentVersion);
  }
}
