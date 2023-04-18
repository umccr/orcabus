import { Construct } from 'constructs';
import { aws_lambda } from 'aws-cdk-lib';
import * as path from 'path';

export class LambdaLayerConstruct extends Construct {
  private readonly _eb_util: aws_lambda.LayerVersion;
  private readonly _schema: aws_lambda.LayerVersion;
  private _all: aws_lambda.LayerVersion[] = [];

  constructor(scope: Construct, id: string) {
    super(scope, id);
    this._eb_util = this.createLambdaLayer('eb_util');  // FIXME refactor, externalise the deps dir, see todo in orcabus-stateless-stack.ts
    this._schema = this.createLambdaLayer('schema');

    this._all.push(this._eb_util);
    this._all.push(this._schema);
  }

  private _build_deps() {
    // TODO using docker SDK to build the deps as part of `cdk synth`, if some `build-auto` flag is true
    //  See https://github.com/umccr/infrastructure/blob/2a1d47c485d11f8a4a9bf0d2cd865f8450164876/cdk/apps/htsget/htsget/goserver.py#L374
  }

  private createLambdaLayer(name: string) {
    return new aws_lambda.LayerVersion(this, 'OrcaBus_' + name + '_LayerVersion', {
      code: aws_lambda.Code.fromAsset(path.join(__dirname, name + '.zip')),
      compatibleRuntimes: [aws_lambda.Runtime.PYTHON_3_9],
      description: 'Lambda layer ' + name + ' for Python 3.9',
    });
  }

  get eb_util(): aws_lambda.LayerVersion {
    return this._eb_util;
  }

  get schema(): aws_lambda.LayerVersion {
    return this._schema;
  }

  get all(): aws_lambda.LayerVersion[] {
    return this._all;
  }
}
