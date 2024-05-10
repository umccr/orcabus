import { IcaEventPipeStackProps } from '../../lib/workload/stateful/stacks/ica-event-pipe/stack';
import { icaEventPipeStackName, eventBusName, icaAwsAccountNumber } from '../constants';

export const getIcaEventPipeStackProps = (): IcaEventPipeStackProps => {
  return {
    name: icaEventPipeStackName,
    eventBusName: eventBusName,
    slackTopicName: 'AwsChatBotTopic',
    icaAwsAccountNumber: icaAwsAccountNumber,
  };
};
