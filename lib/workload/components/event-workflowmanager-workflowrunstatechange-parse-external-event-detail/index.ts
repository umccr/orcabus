import {Construct} from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import {LambdaUuidGeneratorConstruct} from '../lambda-uuid7-generator';
import {PythonWorkflowrunstatechangeLambdaLayerConstruct} from '../python-workflowrunstatechange-lambda-layer';
import {PythonFunction} from '@aws-cdk/aws-lambda-python-alpha';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as events from 'aws-cdk-lib/aws-events';
import * as events_targets from 'aws-cdk-lib/aws-events-targets';
import path from 'path';

export interface WorkflowManagerWorkflowRunStateChangeParseExternalEventDetailProps {
    stateMachinePrefix: string;
    lambdaPrefix: string;
    tableObj: dynamodb.ITableV2;
    tablePartitionName: string;
    eventBusObj: events.IEventBus;
    triggerSource: string;
    triggerStatus: string;
}

export class WorkflowManagerWorkflowRunStateChangeParseExternalEventDetailConstruct extends Construct {
    public readonly stepFunctionObj: sfn.StateMachine;
    public declare detailType: 'workflowRunStateChange';
    public declare outputEventSource: 'orcabus.workflowmanager';

    constructor(
        scope: Construct,
        id: string,
        props: WorkflowManagerWorkflowRunStateChangeParseExternalEventDetailProps
    ) {
        super(scope, id);

        /*
            Part 1 - Generate the two lambdas required for the AWS State Machine
            */

        /* Generate the uuid lambda */
        const lambdaUuid = new LambdaUuidGeneratorConstruct(this, 'LambdaUuidGeneratorConstruct', {
            functionNamePrefix: props.lambdaPrefix,
        }).lambdaObj;

        /* Generate the internal to external event parser */
        const translateEventLayer = new PythonWorkflowrunstatechangeLambdaLayerConstruct(
            this,
            'PythonWorkflowrunstatechangeLambdaLayerConstruct',
            {
                layerName: `${props.lambdaPrefix}-translate-event-layer`,
                layerDescription: 'Layer for the translate event lambda',
            }
        ).lambdaLayerVersionObj;

        /* Generate the internal to external event parser */
        const translateEventLambda = new PythonFunction(this, 'TranslateEventLambda', {
            functionName: `${props.lambdaPrefix}-translate-event`,
            entry: 'lambda/translate_internal_event',
            index: 'translate_internal_event.py',
            runtime: lambda.Runtime.PYTHON_3_11,
            architecture: lambda.Architecture.ARM_64,
            layers: [translateEventLayer],
        });

        /*
            Part 2 - Build the AWS State Machine
            */
        this.stepFunctionObj = new sfn.StateMachine(this, 'StateMachine', {
            stateMachineName: `${props.stateMachinePrefix}-parse-external-event-sfn`,
            definitionBody: sfn.DefinitionBody.fromFile(
                path.join(__dirname, 'step_function_templates', 'parse_external_event.asl.json')
            ),
            definitionSubstitutions: {
                __generate_ref_uuid_lambda_function_arn__: lambdaUuid.currentVersion.functionArn,
                __translate_event_lambda_function_arn__: translateEventLambda.currentVersion.functionArn,
                __table_name__: props.tableObj.tableName,
                __trigger_source__: props.triggerSource,
                __detail_type: this.detailType,
                __event_bus_name__: props.eventBusObj.eventBusName,
                __output_source__: this.outputEventSource,
                __id_type__: props.tablePartitionName,
            },
        });

        /*
            Part 3 - Connect permissions
            */

        /* Allow step functions to invoke the lambda */
        [lambdaUuid, translateEventLambda].forEach((lambdaObj) => {
            lambdaObj.currentVersion.grantInvoke(<iam.IRole>this.stepFunctionObj.role);
        });

        /* Allow step function to write to table */
        props.tableObj.grantReadWriteData(<iam.IRole>this.stepFunctionObj.role);

        /* Allow step function to send events */
        props.eventBusObj.grantPutEventsTo(<iam.IRole>this.stepFunctionObj.role);

        /*
        Part 4 - Set up a rule to trigger the state machine
        */
        const rule = new events.Rule(this, 'workflowrunstatechangeparser_event_rule', {
            eventBus: props.eventBusObj,
            eventPattern: {
                source: [props.triggerSource],
                detailType: [this.detailType],
                detail: {
                    status: [ {"equals-ignore-case": props.triggerStatus} ],
                },
            },
        });

        // Add target of event to be the state machine
        rule.addTarget(
            new events_targets.SfnStateMachine(this.stepFunctionObj, {
                input: events.RuleTargetInput.fromEventPath('$.detail'),
            })
        );
    }
}
