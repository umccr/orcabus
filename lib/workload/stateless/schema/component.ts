import { aws_eventschemas as eventschemas } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { readFileSync } from 'fs';

export interface SchemaConstructProps {
  registryName: string
  schemaName: string,
  schemaDescription: string,
  schemaLocation: string,
  schemaType: string,
}

export class SchemaConstruct extends Construct {

  constructor(scope: Construct, id: string, props: SchemaConstructProps) {
    super(scope, id);
    this.createConstruct(props);
  }

  private createConstruct(props: SchemaConstructProps) {

    const content: string = this.getSchemaContent(props.schemaLocation);

    new eventschemas.CfnSchema(this, props.schemaName, {
      content: content,
      registryName: props.registryName,
      type: props.schemaType,

      // the properties below are optional
      description: props.schemaDescription,
      schemaName: props.schemaName,
    });
  }

  private getSchemaContent(loc: string): string {
    return readFileSync(loc, 'utf-8');
  }

}


interface SchemaProps {
  schemaName: string,
  schemaDescription: string,
  schemaLocation: string,
  schemaType: string
}

export interface MultiSchemaConstructProps {
  registryName: string,
  schemas: SchemaProps[]
}

export class MultiSchemaConstruct extends Construct {

  constructor(scope: Construct, id: string, props: MultiSchemaConstructProps) {
    super(scope, id);
    this.createConstruct(props);
  }


  private createConstruct(props: MultiSchemaConstructProps) {
    props.schemas.forEach(s => {

      new SchemaConstruct(this, s.schemaName, {
        schemaName: s.schemaName,
        schemaDescription: s.schemaDescription,
        schemaLocation: s.schemaLocation,
        schemaType: s.schemaType,
        registryName: props.registryName,
      });
    });
  }
}
