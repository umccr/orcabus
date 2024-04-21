import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { getEnvironmentConfig } from '../../../config/config';
import { EventBusConstruct } from '../../../lib/workload/stateful/stacks/shared/constructs/event-bus';
import { vpcProps } from '../../../config/constants';

let app: cdk.App;
let stack: cdk.Stack;

const constructConfig = getEnvironmentConfig('beta');
if (!constructConfig) throw new Error('No construct config for the test');

app = new cdk.App();
// beforeEach(() => {
//   stack = new cdk.Stack();
// });

test('Test EventBusConstruct Creation', () => {
  stack = new cdk.Stack();
  new EventBusConstruct(
    stack,
    'TestEventBusConstruct',
    constructConfig.stackProps.statefulConfig.sharedStackProps.eventBusProps
  );
  const template = Template.fromStack(stack);

  template.hasResourceProperties('AWS::Events::EventBus', {
    Name: 'OrcaBusMain',
  });
});

test('Test EventBusConstruct Creation with Custom Events Archiver', () => {
  // define test stack account and region for vpc props define
  stack = new cdk.Stack(app, 'TestEventBusStack', {
    env: { account: '123456789', region: 'ap-southeast-2' },
  });
  const eventBusProps = {
    ...constructConfig.stackProps.statefulConfig.sharedStackProps.eventBusProps,

    // add custom event archiver
    addCustomEventArchiver: true,
    archiveBucketName: 'test-archive-bucket',
    lambdaSecurityGroupName: 'test-lambda-security-group',
    vpcProps,
  };
  new EventBusConstruct(stack, 'TestEventBusConstruct', eventBusProps);

  const template = Template.fromStack(stack);

  template.hasResourceProperties('AWS::Events::EventBus', {
    Name: 'OrcaBusMain',
  });
  template.hasResourceProperties('AWS::S3::Bucket', {
    BucketName: 'test-archive-bucket',
  });
  template.hasResourceProperties('AWS::EC2::SecurityGroup', {
    GroupName: 'test-lambda-security-group',
  });
  template.hasResourceProperties('AWS::Lambda::Function', {
    Handler: 'universal_event_archiver.handler',
  });
  template.hasResourceProperties('AWS::Events::Rule', {
    Name: 'UniversalEventArchiverRule',
    EventPattern: {
      account: ['123456789'],
    },
  });
});
