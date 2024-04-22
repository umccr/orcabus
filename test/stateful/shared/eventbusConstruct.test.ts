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
beforeEach(() => {
  stack = new cdk.Stack();
});

test('Test EventBusConstruct Creation With Custome Events Archiver', () => {
  // define test stack account and region for vpc props define
  stack = new cdk.Stack(app, 'TestEventBusStackWithCustomArchiver', {
    env: { account: '123456789', region: 'ap-southeast-2' },
  });

  new EventBusConstruct(
    stack,
    'TestEventBusConstruct',
    constructConfig.stackProps.statefulConfig.sharedStackProps.eventBusProps
  );
  const template = Template.fromStack(stack);

  template.hasResourceProperties('AWS::Events::EventBus', {
    Name: 'OrcaBusMain',
  });
  template.hasResourceProperties('AWS::S3::Bucket', {
    BucketName: 'event-archive-bucket',
  });
  template.hasResourceProperties('AWS::EC2::SecurityGroup', {
    GroupName: 'OrcaBusEventArchiveSecurityGroup',
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

test('Test EventBusConstruct Creation without Custom Events Archiver', () => {
  const eventBusProps = {
    ...constructConfig.stackProps.statefulConfig.sharedStackProps.eventBusProps,

    // remove custom event archiver
    addCustomEventArchiver: false,
  };
  new EventBusConstruct(stack, 'TestEventBusConstructWithoutCustomArchiver', eventBusProps);

  const template = Template.fromStack(stack);

  template.hasResourceProperties('AWS::Events::EventBus', {
    Name: 'OrcaBusMain',
  });

  // check if the custom event archiver is not created
  template.resourceCountIs('AWS::S3::Bucket', 0);
  template.resourceCountIs('AWS::EC2::SecurityGroup', 0);
  template.resourceCountIs('AWS::Lambda::Function', 0);
  template.resourceCountIs('AWS::Events::Rule', 0);
});
