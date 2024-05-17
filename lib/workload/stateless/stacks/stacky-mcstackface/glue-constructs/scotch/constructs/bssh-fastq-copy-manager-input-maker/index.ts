import { Construct } from 'constructs';
import { PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import path from 'path';

/*
Part 2
Input Event Source: `orcabus.workflowrunmanager`
Input Event DetailType: `orcabus.workflowrunstatechange`
Input Event status: `complete`

Output Event source: `orcabus.metadatamanager`
Output Event DetailType: `orcabus.librarystatechange`
Output Event status: `libraryrunidregistered`

* The UpdateDataBaseOnNewSampleSheet Construct
  * Subscribes to the BCLConvertManagerEventHandler Stack outputs and updates the database:
    * Registers all library run ids in the samplesheet
    * Appends libraryrunids to the library ids in the samplesheet
    * For a given library id, queries the current athena database to collect metadata for the library
      * assay
      * type
      * workflow etc.
*/

export interface bsshFastqCopyManagerInputMakerConstructProps {
  layerName?: string;
  layerDescription?: string;
}

export class bsshFastqCopyManagerInputMakerConstruct extends Construct {
  public readonly lambdaLayerArn: string;
  public readonly lambdaLayerVersionObj: PythonLayerVersion;

  constructor(scope: Construct, id: string, props: bsshFastqCopyManagerInputMakerConstructProps) {
    super(scope, id);
    // TODO
  }
}
