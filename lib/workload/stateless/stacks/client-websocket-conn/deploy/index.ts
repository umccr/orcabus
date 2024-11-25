import { Stack, RemovalPolicy, StackProps, Duration } from 'aws-cdk-lib';
import { Table, AttributeType } from 'aws-cdk-lib/aws-dynamodb';
import { Vpc, SecurityGroup, VpcLookupOptions, IVpc, ISecurityGroup } from 'aws-cdk-lib/aws-ec2';
import { WebSocketApi, WebSocketStage } from 'aws-cdk-lib/aws-apigatewayv2';
import { WebSocketLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations';
import { PolicyStatement } from 'aws-cdk-lib/aws-iam';
import { PythonFunction, PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import { Runtime, Architecture, LayerVersion } from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';
import * as path from 'path';
import { WebSocketLambdaAuthorizer } from 'aws-cdk-lib/aws-apigatewayv2-authorizers';
import { StringParameter } from 'aws-cdk-lib/aws-ssm';

export interface WebSocketApiStackProps extends StackProps {
  // DynamoDB and Lambda configuration
  connectionTableName: string;
  websocketApigatewayName: string;
  connectionFunctionName: string;
  disconnectFunctionName: string;
  messageFunctionName: string;
  messageHistoryTableName: string;

  // Parameter name for the WebSocket API endpoint
  websocketApiEndpointParameterName: string;
  websocketStageName: string;

  // Cognito configuration for the authorizer
  cognitoRegion: string;
  cognitoUserPoolIdParameterName: string;
  lambdaSecurityGroupName: string;
  vpcProps: VpcLookupOptions;
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
    const connectionTable = new Table(this, 'WebSocketApiConnections', {
      tableName: props.connectionTableName,
      partitionKey: {
        name: 'connectionId',
        type: AttributeType.STRING,
      },
      removalPolicy: RemovalPolicy.DESTROY, // For demo purposes, not recommended for production
    });

    //DynamoDB Table for message history
    const messageHistoryTable = new Table(this, 'WebSocketApiMessageHistory', {
      tableName: props.messageHistoryTableName,
      partitionKey: {
        name: 'messageId',
        type: AttributeType.STRING,
      },
      timeToLiveAttribute: 'ttl', // Enable TTL
      removalPolicy: RemovalPolicy.DESTROY,
    });

    // Lambda function for $connect
    const connectHandler = this.createPythonFunction(props.connectionFunctionName, {
      index: 'connect.py',
      handler: 'lambda_handler',
      timeout: Duration.minutes(2),
    });

    // Lambda function for $disconnect
    const disconnectHandler = this.createPythonFunction(props.disconnectFunctionName, {
      index: 'disconnect.py',
      handler: 'lambda_handler',
      timeout: Duration.minutes(2),
    });

    // Lambda function for $default (broadcast messages)
    const messageHandler = this.createPythonFunction(props.messageFunctionName, {
      index: 'message.py',
      handler: 'lambda_handler',
      timeout: Duration.minutes(2),
    });

    // build layer from deps
    const authLayer = new PythonLayerVersion(this, 'BaseLayer', {
      entry: path.join(__dirname, '../deps'),
      compatibleRuntimes: [this.lambdaRuntimePythonVersion],
      compatibleArchitectures: [Architecture.ARM_64],
    });

    const userPoolId = StringParameter.fromStringParameterName(
      this,
      'CognitoUserPoolIdParameter',
      props.cognitoUserPoolIdParameterName
    ).stringValue;

    // authorizer function to check the client token based on the JWT token
    const connectAuthorizer = this.createPythonFunction('AuthHandler', {
      index: 'auth.py',
      handler: 'lambda_handler',
      timeout: Duration.minutes(2),
      environment: {
        COGNITO_REGION: props.cognitoRegion,
        COGNITO_USER_POOL_ID: userPoolId,
      },
      layers: [authLayer],
    });

    // Grant permissions to Lambda functions
    connectionTable.grantReadWriteData(connectHandler);
    connectionTable.grantReadWriteData(disconnectHandler);
    connectionTable.grantReadWriteData(messageHandler);
    // messageHistoryTable.grantReadData(connectHandler);
    messageHistoryTable.grantReadWriteData(messageHandler);

    // WebSocket API
    const api = new WebSocketApi(this, props.websocketApigatewayName, {
      apiName: props.websocketApigatewayName,
      description: 'WebSocket API for the app notifications',
      connectRouteOptions: {
        integration: new WebSocketLambdaIntegration('ConnectIntegration', connectHandler),
        // FIXME: uncomment this when auth is implemented
        // authorizer: new WebSocketLambdaAuthorizer(
        //   "ConnectAuthorizer",
        //   connectAuthorizer,
        //   {
        //     authorizerName: "ConnectAuthorizer",
        //     identitySource: [
        //       "route.request.header.Authorization",
        //       "route.request.querystring.Authorization",
        //     ],
        //   }
        // ),
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
      MESSAGE_HISTORY_TABLE: messageHistoryTable.tableName,
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
