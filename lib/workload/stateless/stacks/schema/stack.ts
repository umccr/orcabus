import { Construct } from 'constructs';
import { aws_eventschemas, Stack, StackProps } from 'aws-cdk-lib';
import { readFileSync } from 'fs';

interface SchemaProps {
  schemaName: string;
  schemaDescription: string;
  schemaLocation: string;
  schemaType: string;
}

export interface SchemaStackProps {
  registryName: string;
  schemas: SchemaProps[];
}

/**
 * NOTE:
 * Typically you do not need to modify any CDK code in this stack to add your event schema.
 * See README.md and, follow guideline written in there.
 */

export class SchemaStack extends Stack {
  private readonly registryName: string;

  constructor(scope: Construct, id: string, props: StackProps & SchemaStackProps) {
    super(scope, id, props);

    this.registryName = props.registryName;

    props.schemas.forEach((s) => {
      this.createConstruct(s);
    });
  }

  private createConstruct(props: SchemaProps) {
    const content: string = this.getSchemaContent(props.schemaLocation);

    new aws_eventschemas.CfnSchema(this, props.schemaName, {
      content: content,
      registryName: this.registryName,
      type: props.schemaType,
      description: props.schemaDescription,
      schemaName: props.schemaName,
    });
  }

  private getSchemaContent(loc: string): string {
    return readFileSync(loc, 'utf-8');
  }
}
