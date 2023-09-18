#!/usr/bin/env node

import "source-map-support/register";
import * as cdk from "aws-cdk-lib";
import {FilemanagerStack} from "../stack/filemanager_stack";
import {config} from "dotenv";

config({ path: '../.env' });

export const STACK_NAME = "FilemanagerLocalStack";
const STACK_DESCRIPTION = "A stack deploying filemanager to dev.";

const app = new cdk.App();
new FilemanagerStack(app, STACK_NAME, {
    database_url: process.env.DATABASE_URL ?? throwExpression("DATABASE_URL should not be undefined for localstack development"),
    endpoint_url: process.env.ENDPOINT_URL ?? throwExpression("ENDPOINT_URL should not be undefined for localstack development"),
    stack_name: STACK_NAME
}, {
    stackName: STACK_NAME,
        description: STACK_DESCRIPTION,
    tags: {
    Stack: STACK_NAME,
},
    env: {
        account: "000000000000",
    },
});

function throwExpression(errorMessage: string): never {
    throw new Error(errorMessage);
}