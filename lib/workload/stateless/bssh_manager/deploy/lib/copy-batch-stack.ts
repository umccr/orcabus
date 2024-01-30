import * as cdk from 'aws-cdk-lib';
import {DockerImage, Duration} from 'aws-cdk-lib';
import {Construct} from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
// import {ProcessorMode} from 'aws-cdk-lib/aws-stepfunctions';
// import * as tasks from 'aws-cdk-lib/aws-stepfunctions-tasks';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import {DefinitionBody} from "aws-cdk-lib/aws-stepfunctions";

import {PythonFunction, PythonLayerVersion} from "@aws-cdk/aws-lambda-python-alpha";
import {SSM_PARAMETER_LIST_FOR_WORKFLOW_MANAGER} from "../constants";

// import * as sqs from 'aws-cdk-lib/aws-sqs';
interface CopyBatchStateMachineStackBatchProps extends cdk.StackProps {
    icav2_jwt_ssm_parameter_path: string  // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
}

export class CopyBatchStateMachineStack extends cdk.Stack {

    icav2_jwt_secret_arn_value: string
    icav2_jwt_ssm_parameter_path: string

    constructor(scope: Construct, id: string, props: CopyBatchStateMachineStackBatchProps) {
        super(scope, id, props);

        // Import external ssm parameters
        this.set_jwt_secret_arn_object(props.icav2_jwt_ssm_parameter_path)

        // Define lambda layers
        const lambda_layer = new PythonLayerVersion(this, 'bssh_tool_layer', {
            entry: __dirname + '/../../layers/',
            compatibleRuntimes: [lambda.Runtime.PYTHON_3_11],
            compatibleArchitectures: [lambda.Architecture.X86_64],
            license: 'GPL3',
            description: 'A layer to enable the bssh manager tools layer',
            bundling: {
                commandHooks: {
                    beforeBundling(inputDir: string, outputDir: string): string[] {
                        return []
                    },
                    afterBundling(inputDir: string, outputDir: string): string[] {
                        return [
                            `python -m pip install ${inputDir} -t ${outputDir}`,
                        ];
                    },
                }
            }
        });

        // Define lambdas in this statemachine

        // Manifest inverter lambda
        const manifest_inverter_lambda = new lambda.Function(this, 'manifest_inverter_lambda', {
            runtime: lambda.Runtime.PYTHON_3_11,
            code: lambda.Code.fromAsset(__dirname + '/../../lambdas/manifest_handler'),
            handler: 'handler.handler',
            timeout: Duration.seconds(100),
            memorySize: 1024,
        });

        this.add_icav2_secrets_permissions_to_lambda(
            manifest_inverter_lambda
        )

        // Copy batch data handler lambda
        const copy_batch_data_lambda = new PythonFunction(this, 'copy_batch_data_lambda_python_function', {
            entry: __dirname + '/../../lambdas/copy_batch_data_handler',
            runtime: lambda.Runtime.PYTHON_3_11,
            index: 'handler.py',
            handler: 'handler',
            memorySize: 1024,
            layers: [lambda_layer],
            // @ts-ignore
            timeout: Duration.seconds(20)
        });

        this.add_icav2_secrets_permissions_to_lambda(
            copy_batch_data_lambda
        )

        // Job Status Handler
        const job_status_handler_lambda = new PythonFunction(this, 'job_status_handler_lambda', {
            entry: __dirname + '/../../lambdas/job_status_handler',
            runtime: lambda.Runtime.PYTHON_3_11,
            index: 'handler.py',
            handler: 'handler',
            memorySize: 1024,
            layers: [lambda_layer],
            // @ts-ignore
            timeout: Duration.seconds(20)
        });

        this.add_icav2_secrets_permissions_to_lambda(
            job_status_handler_lambda
        )

        // Specify the statemachine and replace the arn placeholders with the lambda arns defined above
        const stateMachine = new sfn.StateMachine(this, 'copy_batch_state_machine', {
            // defintiontemplate
            definitionBody: DefinitionBody.fromFile(__dirname + "/../../step_functions_templates/copy_batch_state_machine.json"),
            // definitionSubstitutions
            definitionSubstitutions: {
                "__manifest_inverter_lambda_arn__": manifest_inverter_lambda.functionArn,
                "__copy_batch_data_lambda_arn__": copy_batch_data_lambda.functionArn,
                "__job_status_handler_lambda_arn__": job_status_handler_lambda.functionArn,
            }
        });

        // Add execution permissions to stateMachine role
        stateMachine.addToRolePolicy(
            new iam.PolicyStatement(
                {
                    resources: [
                        manifest_inverter_lambda.functionArn,
                        copy_batch_data_lambda.functionArn,
                        job_status_handler_lambda.functionArn,
                    ],
                    actions: [
                        "lambda:InvokeFunction"
                    ]
                }
            )
        )

    }

    private set_jwt_secret_arn_object(icav2_jwt_ssm_parameter_path: string) {
        const icav2_jwt_ssm_parameter = ssm.StringParameter.fromStringParameterName(
            this,
            'get_jwt_secret_arn_value',
            icav2_jwt_ssm_parameter_path
        )

        this.icav2_jwt_ssm_parameter_path = icav2_jwt_ssm_parameter.parameterArn
        this.icav2_jwt_secret_arn_value = icav2_jwt_ssm_parameter.stringValue

    }

    private add_icav2_secrets_permissions_to_lambda(
        lambda_function: lambda.Function | PythonFunction,
    ) {
        /*
        Add the statement that allows
        */
        lambda_function.addToRolePolicy(
            // @ts-ignore
            new iam.PolicyStatement(
                {
                    resources: [
                        this.icav2_jwt_secret_arn_value,
                        this.icav2_jwt_ssm_parameter_path
                    ],
                    actions: [
                        "secretsmanager:GetSecretValue",
                        "ssm:GetParameter"
                    ]
                }
            )
        )
    }
}
