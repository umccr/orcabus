import { Duration } from 'aws-cdk-lib';

// NOTE: this was all set up with some nice typescript types - that separated
// out different postgres settings.. unfortunately - those types are not compatible
// with JSII, so we have had to merge all the fields into one mega Common type.
// Basically this is now all a bit yuck but is necessary to support languages other
// than typescript

export interface PostgresCommon {
  /**
   * The name of the database to create
   */
  readonly name: string;

  /**
   * The name of the admin user to create in the database
   */
  readonly adminUser: string;

  /**
   * If set will override the allocated storage for the db - otherwise
   * we will have this set to smallest database size allowed (20 Gib)
   */
  readonly overrideAllocatedStorage?: number;

  /**
   * If present switches on monitoring features such as postgres
   * logs exported to cloudwatch and performance insights.
   */
  readonly enableMonitoring?: PostgresCommonMonitoring;

  // -------------
  // Settings below are only for serverless Postgres
  // -------------

  /**
   * The minimum number of ACU - or default to the minimum of 0.5
   */
  readonly minCapacity?: number;

  /**
   * The maximum number of ACU - or default to a sensible 4
   */
  readonly maxCapacity?: number;
}

export interface PostgresCommonMonitoring {
  readonly cloudwatchLogsExports: string[];
  readonly enablePerformanceInsights: boolean;
  readonly monitoringInterval: Duration;
}

/**
 * Settings that instruct us to connect an EdgeDb
 * in front of the given postgres instance
 */
export interface EdgeDbCommon {
  /**
   * The version string of EdgeDb that will be used for the spun up EdgeDb image
   */
  readonly version: string;

  /**
   * The memory assigned to the Edge Db service - defaults to a sensible value
   */
  readonly memoryLimitMiB?: number;

  /**
   * The cpu assigned to the Edge Db service - defaults to a sensible value
   */
  readonly cpu?: number;

  /**
   * The port number to assign for EdgeDb protocol - defaults to 5656 which
   * is what is assumed for edgedb connections
   */
  readonly dbPort?: number;
}

export interface EdgeDbPublic {
  /**
   * the DNS prefix to expose the EdgeDb UI as
   */
  readonly urlPrefix: string;

  /**
   * The port number to assign for UI access - defaults to 443. Whilst 443 is
   * entirely sensible - I guess you could add a level of security obscurity by
   * mapping this to another port.
   */
  readonly uiPort?: number;
}
