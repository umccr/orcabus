import { Construct } from 'constructs';
import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as cdk from 'aws-cdk-lib';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import * as lambda from 'aws-cdk-lib/aws-lambda';
// import { showerGlueHandlerConstruct } from './clag';
// import { BclconvertToBsshFastqCopyEventHandlerConstruct } from './elmer';
// import { BsshFastqCopyToBclconvertInteropQcConstruct } from './gorilla';
import { Cttsov2GlueHandlerConstruct } from './jb-weld';
import { WgtsQcGlueHandlerConstruct } from './kwik';
import { TnGlueHandlerConstruct } from './loctite';
import { WtsGlueHandlerConstruct } from './mod-podge';
import { UmccriseGlueHandlerConstruct } from './pva';
import { RnasumGlueHandlerConstruct } from './roket';
import { PieriandxGlueHandlerConstruct } from './nails/';
import { OncoanalyserGlueHandlerConstruct } from './handy-pal';
import { OncoanalyserBothSashGlueHandlerConstruct } from './t-rex';

/*
Provide the glue to get from the bclconvertmanager success event
To triggering the bsshFastqCopyManager
*/

export interface GlueConstructProps {
  /* Event Bus */
  eventBusObj: events.IEventBus;

  /* Tables */
  instrumentRunTableObj: dynamodb.ITableV2;
  cttsov2GlueTableObj: dynamodb.ITableV2;
  wgtsQcGlueTableObj: dynamodb.ITableV2;
  tnGlueTableObj: dynamodb.ITableV2;
  wtsGlueTableObj: dynamodb.ITableV2;
  umccriseGlueTableObj: dynamodb.ITableV2;
  rnasumGlueTableObj: dynamodb.ITableV2;
  pieriandxGlueTableObj: dynamodb.ITableV2;
  oncoanalyserGlueTableObj: dynamodb.ITableV2;
  oncoanalyserBothSashGlueTableObj: dynamodb.ITableV2;

  /* Standard SSM Parameters */
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
  analysisOutputUriSsmParameterObj: ssm.IStringParameter;
  analysisCacheUriSsmParameterObj: ssm.IStringParameter;
  analysisLogsUriSsmParameterObj: ssm.IStringParameter;

  /* Secrets */
  icav2AccessTokenSecretObj: secretsManager.ISecret;

  /* BSSH SSM Parameters */
  bsshOutputFastqCopyOutputUriSsmParameterObj: ssm.IStringParameter;

  /* PierianDX SSM Parameters */
  pieriandxProjectInfoSsmParameterObj: ssm.IStringParameter;
  redcapLambdaObj: lambda.IFunction;
}

export class GlueConstruct extends Construct {
  constructor(scope: Construct, id: string, props: GlueConstructProps) {
    super(scope, id);

    /*
    Part A: Send 'showered' events if a new samplesheet arrives or new fastq list rows arrive
    */
    // const clag = new showerGlueHandlerConstruct(this, 'clag', {
    //   /* Event Bus */
    //   eventBusObj: props.eventBusObj,
    //   /* Tables */
    //   instrumentRunTableObj: props.instrumentRunTableObj,
    //   /* Secrets */
    //   icav2AccessTokenSecretObj: props.icav2AccessTokenSecretObj,
    // });

    /*
    Part B: Copy the fastq list rows by connecting the bclconvert manager completion with the bsshfastqcopy manager
    */
    // const elmer = new BclconvertToBsshFastqCopyEventHandlerConstruct(this, 'elmer', {
    //   /* Event Bus */
    //   eventBusObj: props.eventBusObj,
    //   /* SSM Parameters */
    //   bsshOutputFastqCopyUriSsmParameterObj: props.bsshOutputFastqCopyOutputUriSsmParameterObj,
    //   /* Secrets */
    //   icav2AccessTokenSecretObj: props.icav2AccessTokenSecretObj,
    // });

    /*
    Part C: Connect the bclconvert interop qc
    */
    // const gorilla = new BsshFastqCopyToBclconvertInteropQcConstruct(this, 'gorilla', {
    //   /* Event Objects */
    //   eventBusObj: props.eventBusObj,
    //   /* SSM Parameter Objects */
    //   analysisLogsUriSsmParameterObj: props.analysisLogsUriSsmParameterObj,
    //   analysisOutputUriSsmParameterObj: props.analysisOutputUriSsmParameterObj,
    //   icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
    //   /* Secrets */
    //   icav2AccessTokenSecretObj: props.icav2AccessTokenSecretObj,
    // });

    /*
    Part D: Plumber-up the oncoanalyser services
    */
    const handyPal = new OncoanalyserGlueHandlerConstruct(this, 'handyPal', {
      /* Event Objects */
      eventBusObj: props.eventBusObj,
      /* Tables */
      oncoanalyserGlueTableObj: props.oncoanalyserGlueTableObj,
      /* SSM Parameter Objects */
      analysisCacheUriSsmParameterObj: props.analysisCacheUriSsmParameterObj,
      analysisLogsUriSsmParameterObj: props.analysisLogsUriSsmParameterObj,
      analysisOutputUriSsmParameterObj: props.analysisOutputUriSsmParameterObj,
    });

    /*
    Part D: Plumber-up the cttso v2 to the shower services
    */
    const jb_weld = new Cttsov2GlueHandlerConstruct(this, 'jb_weld', {
      /* Event Bus */
      eventBusObj: props.eventBusObj,
      /* Tables */
      cttsov2GlueTableObj: props.cttsov2GlueTableObj,
      /* SSM Parameters */
      icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
      analysisOutputUriSsmParameterObj: props.analysisOutputUriSsmParameterObj,
      analysisCacheUriSsmParameterObj: props.analysisCacheUriSsmParameterObj,
      analysisLogsUriSsmParameterObj: props.analysisLogsUriSsmParameterObj,
      /* Secrets */
      icav2AccessTokenSecretObj: props.icav2AccessTokenSecretObj,
    });

    /*
    Part E: Plumber-up the WGTS QC Execution Service to the shower services
    */
    const kwik = new WgtsQcGlueHandlerConstruct(this, 'kwik', {
      /* Event Bus */
      eventBusObj: props.eventBusObj,
      /* Tables */
      wgtsQcGlueTableObj: props.wgtsQcGlueTableObj,
      /* SSM Parameters */
      icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
      analysisOutputUriSsmParameterObj: props.analysisOutputUriSsmParameterObj,
      analysisCacheUriSsmParameterObj: props.analysisCacheUriSsmParameterObj,
      analysisLogsUriSsmParameterObj: props.analysisLogsUriSsmParameterObj,
      /* Secrets */
      icav2AccessTokenSecretObj: props.icav2AccessTokenSecretObj,
    });

    /*
    Part F: Plumber-up the Tumor-Normal Execution Service to the shower services
    */
    const loctite = new TnGlueHandlerConstruct(this, 'loctite', {
      /* Event Bus */
      eventBusObj: props.eventBusObj,
      /* Tables */
      tnGlueTableObj: props.tnGlueTableObj,
      /* SSM Parameters */
      icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
      analysisOutputUriSsmParameterObj: props.analysisOutputUriSsmParameterObj,
      analysisLogsUriSsmParameterObj: props.analysisLogsUriSsmParameterObj,
      analysisCacheUriSsmParameterObj: props.analysisCacheUriSsmParameterObj,
      /* Secrets */
      icav2AccessTokenSecretObj: props.icav2AccessTokenSecretObj,
    });

    /*
    Part G: Plumber-up the WTS Execution Service to the shower services
    */
    const modPodge = new WtsGlueHandlerConstruct(this, 'modPodge', {
      /* Event Bus */
      eventBusObj: props.eventBusObj,
      /* Tables */
      wtsGlueTableObj: props.wtsGlueTableObj,
      /* SSM Parameters */
      icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
      analysisOutputUriSsmParameterObj: props.analysisOutputUriSsmParameterObj,
      analysisLogsUriSsmParameterObj: props.analysisLogsUriSsmParameterObj,
      analysisCacheUriSsmParameterObj: props.analysisCacheUriSsmParameterObj,
      /* Secrets */
      icav2AccessTokenSecretObj: props.icav2AccessTokenSecretObj,
    });

    /*
    Part H: Plumber-up the cttsov2 to pieriandx services
    */
    const nails = new PieriandxGlueHandlerConstruct(this, 'nails', {
      /* Event Bus */
      eventBusObj: props.eventBusObj,

      /* Tables */
      pieriandxGlueTableObj: props.pieriandxGlueTableObj,

      /* Secrets */
      icav2AccessTokenSecretObj: props.icav2AccessTokenSecretObj,

      /* Extras */
      pieriandxProjectInfoSsmParameterObj: props.pieriandxProjectInfoSsmParameterObj,
      redcapLambdaObj: props.redcapLambdaObj,
    });

    /*
    Part I: Plumber-up the UMCCRise Execution Service to the shower services
    */
    const pva = new UmccriseGlueHandlerConstruct(this, 'pva', {
      /* Event Bus */
      eventBusObj: props.eventBusObj,
      /* Tables */
      umccriseGlueTableObj: props.umccriseGlueTableObj,
      /* SSM Parameters */
      icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
      analysisOutputUriSsmParameterObj: props.analysisOutputUriSsmParameterObj,
      analysisLogsUriSsmParameterObj: props.analysisLogsUriSsmParameterObj,
      analysisCacheUriSsmParameterObj: props.analysisCacheUriSsmParameterObj,
      /* Secrets */
      icav2AccessTokenSecretObj: props.icav2AccessTokenSecretObj,
    });

    /*
    Part J: Plumber-up the RNASum Execution Service to the shower services
    */
    const roket = new RnasumGlueHandlerConstruct(this, 'roket', {
      /* Event Bus */
      eventBusObj: props.eventBusObj,
      /* Tables */
      rnasumGlueTableObj: props.rnasumGlueTableObj,
      /* SSM Parameters */
      icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
      analysisOutputUriSsmParameterObj: props.analysisOutputUriSsmParameterObj,
      analysisLogsUriSsmParameterObj: props.analysisLogsUriSsmParameterObj,
      analysisCacheUriSsmParameterObj: props.analysisCacheUriSsmParameterObj,
      /* Secrets */
      icav2AccessTokenSecretObj: props.icav2AccessTokenSecretObj,
    });

    /*
    Part K: Plumber up the oncoanalyser-wgts-dna-rna and sash service - both
    have the same entry point so we can use the same construct
    */
    const tRex = new OncoanalyserBothSashGlueHandlerConstruct(this, 'trex', {
      /* Event Objects */
      eventBusObj: props.eventBusObj,
      /* Tables */
      oncoanalyserBothSashGlueTableObj: props.oncoanalyserBothSashGlueTableObj,
      /* SSM Parameter Objects */
      analysisCacheUriSsmParameterObj: props.analysisCacheUriSsmParameterObj,
      analysisLogsUriSsmParameterObj: props.analysisLogsUriSsmParameterObj,
      analysisOutputUriSsmParameterObj: props.analysisOutputUriSsmParameterObj,
    });
  }
}

export interface GlueStackConfig {
  /* Event Bus */
  eventBusName: string;

  /* Tables */
  instrumentRunTableName: string;
  cttsov2GlueTableName: string;
  wgtsQcGlueTableName: string;
  tnGlueTableName: string;
  wtsGlueTableName: string;
  umccriseGlueTableName: string;
  rnasumGlueTableName: string;
  pieriandxGlueTableName: string;
  oncoanalyserGlueTableName: string;
  oncoanalyserBothSashGlueTableName: string;

  /* SSM Parameters */
  icav2ProjectIdSsmParameterName: string;
  analysisCacheUriSsmParameterName: string;
  analysisOutputUriSsmParameterName: string;
  analysisLogsUriSsmParameterName: string;

  /* Secrets */
  icav2AccessTokenSecretName: string;

  /* BSSH SSM Parameters */
  bsshOutputFastqCopyUriSsmParameterName: string;

  /* PierianDX SSM Parameters */
  pieriandxProjectInfoSsmParameterPath: string;

  /* PierianDX External Functions */
  redcapLambdaFunctionName: string;
}

export type GlueStackProps = GlueStackConfig & cdk.StackProps;

export class GlueStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: GlueStackProps) {
    super(scope, id, props);

    /*
    Part 0: Get the inputs as objects
    */

    /*
    Get the event bus
    */
    const eventBusObj = events.EventBus.fromEventBusName(this, 'eventBusObj', props.eventBusName);

    /*
    Get the tables
    */
    const instrumentRunTableObj = dynamodb.Table.fromTableName(
      this,
      'instrumentRunTableObj',
      props.instrumentRunTableName
    );
    const cttsov2GlueTableObj = dynamodb.Table.fromTableName(
      this,
      'cttsov2GlueTableObj',
      props.cttsov2GlueTableName
    );
    const wgtsQcGlueTableObj = dynamodb.Table.fromTableName(
      this,
      'wgtsQcGlueTableObj',
      props.wgtsQcGlueTableName
    );
    const tnGlueTableObj = dynamodb.Table.fromTableName(
      this,
      'tnGlueTableObj',
      props.tnGlueTableName
    );
    const wtsGlueTableObj = dynamodb.Table.fromTableName(
      this,
      'wtsGlueTableObj',
      props.wtsGlueTableName
    );
    const umccriseGlueTableObj = dynamodb.Table.fromTableName(
      this,
      'umccriseGlueTableObj',
      props.umccriseGlueTableName
    );
    const rnasumGlueTableObj = dynamodb.Table.fromTableName(
      this,
      'rnasumGlueTableObj',
      props.rnasumGlueTableName
    );
    const pieriandxGlueTableObj = dynamodb.Table.fromTableName(
      this,
      'pieriandxGlueTableObj',
      props.pieriandxGlueTableName
    );
    const oncoanalyserGlueTableObj = dynamodb.Table.fromTableName(
      this,
      'oncoanalyserGlueTableObj',
      props.oncoanalyserGlueTableName
    );
    const oncoanalyserBothSashGlueTableObj = dynamodb.Table.fromTableName(
      this,
      'oncoanalyserBothSashGlueTableObj',
      props.oncoanalyserBothSashGlueTableName
    );

    /*
    Get the SSM Parameters
    */
    const icav2ProjectIdSsmParameterObj = ssm.StringParameter.fromStringParameterName(
      this,
      'icav2ProjectIdSsmParameterObj',
      props.icav2ProjectIdSsmParameterName
    );

    const analysisCacheUriSsmParameterObj = ssm.StringParameter.fromStringParameterName(
      this,
      'analysisCacheUriPrefixSsmParameterObj',
      props.analysisCacheUriSsmParameterName
    );
    const analysisOutputUriSsmParameterObj = ssm.StringParameter.fromStringParameterName(
      this,
      'analysisOutputUriPrefixSsmParameterObj',
      props.analysisOutputUriSsmParameterName
    );

    const analysisLogsUriSsmParameterObj = ssm.StringParameter.fromStringParameterName(
      this,
      'analysisLogsUriPrefixSsmParameterObj',
      props.analysisLogsUriSsmParameterName
    );

    /*
    Secrets
    */
    const icav2AccessTokenSecretObj = secretsManager.Secret.fromSecretNameV2(
      this,
      'icav2AccessTokenSecretObj',
      props.icav2AccessTokenSecretName
    );

    /*
    BSSH SSM Parameters
    */
    const bsshOutputFastqCopyUriSsmParameterObj = ssm.StringParameter.fromStringParameterName(
      this,
      'bsshOutputFastqCopyUriPrefixSsmParameterObj',
      props.bsshOutputFastqCopyUriSsmParameterName
    );

    /*
    PierianDx SSM Parameters
    */
    const pieriandxProjectInfoSsmParameterObj = ssm.StringParameter.fromStringParameterName(
      this,
      'pieriandxProjectInfoSsmParameterObj',
      props.pieriandxProjectInfoSsmParameterPath
    );

    /*
    PierianDx External Functions
    */
    const redcapLambdaObj = lambda.Function.fromFunctionName(
      this,
      'redcapLambdaObj',
      props.redcapLambdaFunctionName
    );

    /*
    Call the construct
    */
    new GlueConstruct(this, 'stacky_glue', {
      /* Event stuff */
      eventBusObj: eventBusObj,

      /* Tables */
      instrumentRunTableObj: instrumentRunTableObj,
      wgtsQcGlueTableObj: wgtsQcGlueTableObj,
      cttsov2GlueTableObj: cttsov2GlueTableObj,
      tnGlueTableObj: tnGlueTableObj,
      wtsGlueTableObj: wtsGlueTableObj,
      umccriseGlueTableObj: umccriseGlueTableObj,
      rnasumGlueTableObj: rnasumGlueTableObj,
      pieriandxGlueTableObj: pieriandxGlueTableObj,
      oncoanalyserGlueTableObj: oncoanalyserGlueTableObj,
      oncoanalyserBothSashGlueTableObj: oncoanalyserBothSashGlueTableObj,

      /* SSM Parameters */
      icav2ProjectIdSsmParameterObj: icav2ProjectIdSsmParameterObj,
      analysisOutputUriSsmParameterObj: analysisOutputUriSsmParameterObj,
      analysisCacheUriSsmParameterObj: analysisCacheUriSsmParameterObj,
      analysisLogsUriSsmParameterObj: analysisLogsUriSsmParameterObj,

      /* Secrets */
      icav2AccessTokenSecretObj: icav2AccessTokenSecretObj,

      /* BSSH SSM Parameters */
      bsshOutputFastqCopyOutputUriSsmParameterObj: bsshOutputFastqCopyUriSsmParameterObj,

      /* PierianDx SSM Parameters */
      pieriandxProjectInfoSsmParameterObj: pieriandxProjectInfoSsmParameterObj,

      /* PierianDx External Functions */
      redcapLambdaObj: redcapLambdaObj,
    });
  }
}
