import { IcaEventPipeStackProps } from '../../lib/workload/stateful/stacks/ica-event-pipe/stack';
import { eventBusName, icaAwsAccountNumber, slackTopicName } from '../constants';

export const getIcaEventPipeStackProps = (): IcaEventPipeStackProps => {
  return {
    name: 'IcaEventPipeStack',
    eventBusName: eventBusName,
    slackTopicName: slackTopicName,
    icaAwsAccountNumber: icaAwsAccountNumber,
  };
};
