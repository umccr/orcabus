#!/usr/bin/env python
import boto3
from libica.app import gds

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

def get_umccr_icav1_jwt():
	client = boto3.client('secretsmanager')
	return client.get_secret_value('IcaSecretsPortal')

def main():
	_success, creds = gds.get_folder_cred('fol.3ff7cdb1c3014da9627208d89d4636ab') # gds://development
	update_ssm(creds)

if __name__ == '__main__':
	main()