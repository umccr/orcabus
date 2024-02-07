# Deployment of filemanager

This folder contains CDK deployment code for filemanager. The CDK code can be deployed using `cdk`:

```sh
npm install
cdk bootstrap
cdk deploy
```

By default, the stack does not perform database migration. To migrate the database, use the script inside `package.json`:

```sh
npm run migrate -- cdk deploy
```

or set `FILEMANAGER_DEPLOY_DATABASE_MIGRATION`:

```sh
export FILEMANAGER_DEPLOY_DATABASE_MIGRATION="true"
```
