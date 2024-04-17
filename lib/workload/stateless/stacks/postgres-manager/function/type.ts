/**
 * There are 2 ways of connecting from microservice to db
 */
export enum DbAuthType {
  RDS_IAM,
  USERNAME_PASSWORD,
}

export type EventType = {
  microserviceName: string;
};

export type MicroserviceConfig = {
  name: string;
  authType: DbAuthType;
}[];
