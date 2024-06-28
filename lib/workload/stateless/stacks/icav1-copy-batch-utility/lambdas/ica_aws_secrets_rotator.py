#!/usr/bin/env python
import boto3
# from libica.app import gds
from libica.openapi import libgds

def update_ssm(creds):
	client = boto3.client('ssm')
	creds = vars(creds) # from opaque object to subscriptable dict

	aws_access_key_id = creds['_access_key_id']
	aws_secret_access_key = creds['_secret_access_key']
	aws_session_token = creds['_session_token']

	parameters = [
		{
			'Name': 'icav1_aws_access_key_id',
			'Description': 'ICAv1 AWS Access Key ID',
			'Value': aws_access_key_id,
			'Type': 'SecureString',
			'Overwrite': True
		},
		{
			'Name': 'icav1_aws_secret_access_key',
			'Description': 'ICAv1 AWS Secret Access Key',
			'Value': aws_secret_access_key,
			'Type': 'SecureString',
			'Overwrite': True
		},
		{
			'Name': 'icav1_aws_session_token',
			'Description': 'ICAv1 AWS Session Token',
			'Value': aws_session_token,
			'Type': 'SecureString',
			'Overwrite': True
		}
	]

	for parameter in parameters:
		client.put_parameter(**parameter)

	print("ICAv1 AWS secrets updated successfully")

def get_umccr_icav1_jwt():
	client = boto3.client('secretsmanager')
	return client.get_secret_value(SecretId='IcaSecretsPortal') # pragma: allowlist secret

def handler(_event, _context):
	ica_access_token = get_umccr_icav1_jwt()

	configuration = libgds.Configuration(
		host="https://aps2.platform.illumina.com",
		api_key={
			'Authorization': ica_access_token['SecretString']
		},
		api_key_prefix={
			'Authorization': "Bearer"
		},
	)

	with libgds.ApiClient(configuration) as gds_client:
		folders_api = libgds.FoldersApi(gds_client)
		folder_id = 'fol.3ff7cdb1c3014da9627208d89d4636ab' # gds://development

		try:
			resp: libgds.FolderResponse = folders_api.update_folder(folder_id=folder_id, include='objectStoreAccess')
			cred: libgds.AwsS3TemporaryUploadCredentials = resp.object_store_access.aws_s3_temporary_upload_credentials
			update_ssm(cred)
		except libgds.ApiException as e:
			message = f"Failed to get temporary credentials for GDS folder ID ({folder_id}). Exception - {e}"
			print(message)
# if __name__ == '__main__':
# 	handler(None, None)