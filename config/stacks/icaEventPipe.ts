import { IcaEventPipeStackProps } from '../../lib/workload/stateful/stacks/ica-event-pipe/stack';
import { eventBusName } from '../constants';

export const getIcaEventPipeStackProps = (): IcaEventPipeStackProps => {
  return {
    name: 'IcaEventPipeStack',
    eventBusName: eventBusName,
    slackTopicName: 'AwsChatBotTopic',
  };
};
