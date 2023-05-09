import { Construct } from 'constructs';
import { aws_eventschemas as eventschemas } from 'aws-cdk-lib';

export interface SchemaRegistryProps {
  registryName: string,
  description: string
}

export class SchemaRegistryConstruct extends Construct {

  constructor(scope: Construct, id: string, props: SchemaRegistryProps) {
    super(scope, id);
    this.createConstruct(props);
  }

  private createConstruct(props: SchemaRegistryProps) {

    const cfnRegistry = new eventschemas.CfnRegistry(this, props.registryName, {
      description: props.description,
      registryName: props.registryName,
    });
  }

}
