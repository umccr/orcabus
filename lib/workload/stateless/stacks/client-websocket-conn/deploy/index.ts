import { Stack, RemovalPolicy, StackProps, Duration } from 'aws-cdk-lib';
import { Table, AttributeType } from 'aws-cdk-lib/aws-dynamodb';
import { Vpc, SecurityGroup, VpcLookupOptions, IVpc, ISecurityGroup } from 'aws-cdk-lib/aws-ec2';
import { WebSocketApi, WebSocketStage } from 'aws-cdk-lib/aws-apigatewayv2';
import { WebSocketLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations';
import { PolicyStatement } from 'aws-cdk-lib/aws-iam';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { Runtime, Architecture } from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';
import * as path from 'path';
import { StringParameter } from 'aws-cdk-lib/aws-ssm';

export interface WebSocketApiStackProps extends StackProps {
  connectionTableName: string;
  websocketApigatewayName: string;

  lambdaSecurityGroupName: string;
  vpcProps: VpcLookupOptions;

  websocketApiEndpointParameterName: string;
  websocketStageName: string;
}

export class WebSocketApiStack extends Stack {
  private readonly lambdaRuntimePythonVersion = Runtime.PYTHON_3_12;
  private readonly props: WebSocketApiStackProps;
  private vpc: IVpc;
  private lambdaSG: ISecurityGroup;

  constructor(scope: Construct, id: string, props: WebSocketApiStackProps) {
    super(scope, id, props);

    this.props = props;

    this.vpc = Vpc.fromLookup(this, 'MainVpc', props.vpcProps);
    this.lambdaSG = SecurityGroup.fromLookupByName(
      this,
      'LambdaSecurityGroup',
      props.lambdaSecurityGroupName,
      this.vpc
    );

    // DynamoDB Table for storing connection IDs
    const connectionTable = new Table(this, 'WebSocketConnections', {
      tableName: props.connectionTableName,
      partitionKey: {
        name: 'ConnectionId',
        type: AttributeType.STRING,
      },
      removalPolicy: RemovalPolicy.DESTROY, // For demo purposes, not recommended for production
    });

    // DynamoDB Table for message history
    // const messageHistoryTable = new Table(this, "WebSocketMessageHistory", {
    //   partitionKey: {
    //     name: "messageId",
    //     type: AttributeType.STRING,
    //   },
    //   timeToLiveAttribute: "ttl", // Enable TTL
    //   removalPolicy: RemovalPolicy.DESTROY,
    // });

    // Lambda function for $connect
    const connectHandler = this.createPythonFunction('connectHandler', {
      index: 'connect.py',
      handler: 'lambda_handler',
      timeout: Duration.minutes(2),
    });

    // Lambda function for $disconnect
    const disconnectHandler = this.createPythonFunction('disconnectHandler', {
      index: 'disconnect.py',
      handler: 'lambda_handler',
      timeout: Duration.minutes(2),
    });

    // Lambda function for $default (broadcast messages)
    const messageHandler = this.createPythonFunction('messageHandler', {
      index: 'message.py',
      handler: 'lambda_handler',
      timeout: Duration.minutes(2),
    });

    // Grant permissions to Lambda functions
    connectionTable.grantReadWriteData(connectHandler);
    connectionTable.grantReadWriteData(disconnectHandler);
    connectionTable.grantReadWriteData(messageHandler);
    // messageHistoryTable.grantReadData(connectHandler);
    // messageHistoryTable.grantReadWriteData(messageHandler);

    // WebSocket API
    const api = new WebSocketApi(this, props.websocketApigatewayName, {
      apiName: props.websocketApigatewayName,
      connectRouteOptions: {
        integration: new WebSocketLambdaIntegration('ConnectIntegration', connectHandler),
      },
      disconnectRouteOptions: {
        integration: new WebSocketLambdaIntegration('DisconnectIntegration', disconnectHandler),
      },
      defaultRouteOptions: {
        integration: new WebSocketLambdaIntegration('DefaultIntegration', messageHandler),
      },
    });

    api.addRoute('sendMessage', {
      integration: new WebSocketLambdaIntegration('SendMessageIntegration', messageHandler),
    });

    // Deploy WebSocket API to a stage
    const stage = new WebSocketStage(this, 'WebSocketStage', {
      webSocketApi: api,
      stageName: props.websocketStageName,
      autoDeploy: true,
    });

    // Create the WebSocket API endpoint URL
    const webSocketApiEndpoint = `${api.apiEndpoint}/${stage.stageName}`;

    // save this url into the parameter store for the client to use
    new StringParameter(this, 'WebSocketApiEndpoint', {
      parameterName: props.websocketApiEndpointParameterName,
      description: 'The endpoint URL for the WebSocket API',
      stringValue: webSocketApiEndpoint,
    });

    const commonEnvironment = {
      CONNECTION_TABLE: connectionTable.tableName,
      // MESSAGE_HISTORY_TABLE: messageHistoryTable.tableName,
      WEBSOCKET_API_ENDPOINT: webSocketApiEndpoint,
    };

    // Add environment variables individually
    for (const [key, value] of Object.entries(commonEnvironment)) {
      connectHandler.addEnvironment(key, value);
      disconnectHandler.addEnvironment(key, value);
      messageHandler.addEnvironment(key, value);
    }

    // Grant permissions to the message handler
    messageHandler.addToRolePolicy(
      new PolicyStatement({
        actions: ['execute-api:ManageConnections'],
        resources: [
          `arn:aws:execute-api:${this.region}:${this.account}:${api.apiId}/dev/POST/@connections/*`,
        ],
      })
    );
  }

  private createPythonFunction(name: string, props: object): PythonFunction {
    return new PythonFunction(this, name, {
      entry: path.join(__dirname, '../lambda'),
      runtime: this.lambdaRuntimePythonVersion,
      securityGroups: [this.lambdaSG],
      vpc: this.vpc,
      vpcSubnets: { subnets: this.vpc.privateSubnets },
      architecture: Architecture.ARM_64,
      ...props,
    });
  }
}
