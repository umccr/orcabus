#!/usr/bin/env node

import "source-map-support/register";
import * as cdk from "aws-cdk-lib";
import {FilemanagerStack} from "../stack/filemanager_stack";

export const STACK_NAME = "FilemanagerLocalStack";
const STACK_DESCRIPTION = "A stack deploying filemanager to dev.";

const app = new cdk.App();
new FilemanagerStack(app, STACK_NAME, {
    database_url: "postgresql://filemanager:filemanager@db:5432/filemanager",
    endpoint_url: "http://localstack:4566",
    force_path_style: true,
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