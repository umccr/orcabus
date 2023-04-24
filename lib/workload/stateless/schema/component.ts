// TODO create a CDK Construct
//  that create AWS resources such as
//  aws_eventschemas.CfnRegistry  (this is L1) -- check whether we have L2 construct, etc..
//  then, create each schema and add into this registry

// TODO discussions:
//  1. CfnRegistry is stateful resource or, we create as part of self mutating pipeline?
//  2. then, we create these schema from JSON file more centrally into this registry

import { aws_eventschemas as eventschemas } from 'aws-cdk-lib';
import {Construct} from "constructs";

export interface SchemaConstructProps {
  registryName: string
  schemaName: string,
  schemaDescription: string,
  schemaLocation: string
}
export class SchemaConstruct extends Construct {

    constructor(scope: Construct, id: string, cProps: SchemaConstructProps) {
    super(scope, id);
    this.createConstruct(cProps);
    console.log(this.node.tryGetContext())
  }

  private createConstruct(cProps: SchemaConstructProps) {

    // import * as content from cProps.schemaLocation;
    console.log(cProps.schemaLocation)

    const cfnSchema = new eventschemas.CfnSchema(this, cProps.schemaName, {
      content: "", // content,
      // content=json.dumps(get_schema_json_as_dict(f"schema/{name}.json")),
      registryName: cProps.registryName,
      type: 'OpenApi3',

      // the properties below are optional
      description: cProps.schemaDescription,
      schemaName: cProps.schemaName
    });
  }

}


interface SchemaProps {
    schemaName: string,
    schemaDescription: string,
    schemaLocation: string
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
        registryName: props.registryName
      })
    });

  }

}
