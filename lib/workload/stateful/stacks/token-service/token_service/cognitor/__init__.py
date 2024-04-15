# -*- coding: utf-8 -*-
import random
import string
from dataclasses import dataclass

import boto3


@dataclass
class ServiceUserDto:
    username: str
    password: str
    email: str


class CognitoTokenService:

    def __init__(self, user_pool_id: str, user_pool_app_client_id: str):
        self.client = boto3.client('cognito-idp')
        self.user_pool_id: str = user_pool_id
        self.user_pool_app_client_id: str = user_pool_app_client_id

    @staticmethod
    def generate_password(length: int = 32) -> str:
        """
        Must meet the Cognito password requirements policy
        https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-policies.html
        """
        if length < 8:
            raise ValueError('Length must be at least 8 characters or more better')
        return ''.join(
            random.SystemRandom().choice(string.ascii_letters + string.digits + '_-!@#%&.') for _ in range(length)
        )

    def list_users(self, **kwargs) -> dict:
        if 'UserPoolId' in kwargs.keys():
            kwargs.pop('UserPoolId')
        return self.client.list_users(
            UserPoolId=self.user_pool_id,
            **kwargs
        )

    def disable_user(self, username: str) -> dict:
        return self.client.admin_disable_user(
            UserPoolId=self.user_pool_id,
            Username=username
        )

    def enable_user(self, username: str) -> dict:
        return self.client.admin_enable_user(
            UserPoolId=self.user_pool_id,
            Username=username
        )

    def delete_user(self, username: str):
        self.client.admin_delete_user(
            UserPoolId=self.user_pool_id,
            Username=username
        )

    def get_user(self, username: str) -> dict:
        return self.client.admin_get_user(
            UserPoolId=self.user_pool_id,
            Username=username
        )

    def username_exists(self, username: str) -> bool:
        try:
            resp = self.get_user(username=username)
            return resp['Username'] == username
        except self.client.exceptions.UserNotFoundException:
            return False

    def register_service_user(self, user_dto: ServiceUserDto):
        """
        Register new service user if it does not exist in the Cognito User Pool database. If the user already exists,
        it will skip and do nothing. Required admin permission or more precisely the actions required are:
            'cognito-idp:SignUp'
            'cognito-idp:AdminConfirmSignUp'
        """
        if self.username_exists(user_dto.username):
            return

        resp_signup = self.client.sign_up(
            ClientId=self.user_pool_app_client_id,
            Username=user_dto.username,
            Password=user_dto.password,
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': user_dto.email
                },
            ],
        )

        user_sub = resp_signup['UserSub']

        if user_sub:
            _ = self.client.admin_confirm_sign_up(
                UserPoolId=self.user_pool_id,
                Username=user_dto.username,
            )

    def generate_service_user_tokens(self, user_dto: ServiceUserDto) -> dict:
        """
        Generate Service User tokens using Cognito `USER_PASSWORD_AUTH` authentication flow and, return a new dict
        object having the following:
        {
            'id_token': <mandatory: jwt token; non revoke-able 24 hours max validity>,
            'refresh_token': <optional: refresh token to extend id_token life; revoke-able; can be longer validity>,
            'access_token': <optional: access token for this ID>,
            'token_type': <optional: token type e.g. Bearer>,
            'expires_in': <optional: in seconds>,
        }
        """
        d = {}

        response: dict = self.client.initiate_auth(
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': user_dto.username,
                'PASSWORD': user_dto.password,
            },
            ClientId=self.user_pool_app_client_id,
        )

        if response and 'AuthenticationResult' in response.keys():
            r = response['AuthenticationResult']
            d.update(id_token=r['IdToken'])   # this is the JWT that all we need...

            # Note: intentionally commented out the following tokens for future potential expansion use cases

            # d.update(refresh_token=r['RefreshToken'])
            # d.update(access_token=r['AccessToken'])
            # d.update(token_type=r['TokenType'])
            # d.update(expires_in=r['ExpiresIn'])

        return d

    def rotate_service_user_password(self, user_dto: ServiceUserDto):
        """
        Forced set Cognito Service User login credential info from pass-in dto
        """
        self.client.admin_set_user_password(
            UserPoolId=self.user_pool_id,
            Username=user_dto.username,
            Password=user_dto.password,
            Permanent=True
        )
