import { Construct } from 'constructs';
import { aws_eventschemas as eventschemas } from 'aws-cdk-lib';

export interface Props {
  registryName: string,
  description: string
}

export class SchemaRegistryConstruct extends Construct {

  constructor(scope: Construct, id: string, props: Props) {
    super(scope, id);
    this.createConstruct(props);
  }

  private createConstruct(props: Props) {

	const cfnRegistry = new eventschemas.CfnRegistry(this, props.registryName, {
	  description: props.description,
	  registryName: props.registryName
	});
  }

}
