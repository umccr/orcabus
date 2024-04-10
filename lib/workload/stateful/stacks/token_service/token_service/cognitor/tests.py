import logging
import unittest
from datetime import datetime

import botocore
from botocore.stub import Stubber

from . import CognitoTokenService, ServiceUserDto

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class CognitorUnitTest(unittest.TestCase):

    def setUp(self):
        self.srv = CognitoTokenService(
            user_pool_id="mock_pool_id",
            user_pool_app_client_id="mock_client_id"
        )

        self.jjb_dto = ServiceUserDto(
            username='jjb',
            email='<EMAIL>',
            password=CognitoTokenService.generate_password()
        )

        self.mock_client = botocore.session.get_session().create_client('cognito-idp')
        self.srv.client = self.mock_client

    def test_token_service(self):
        """
        python -m unittest token_service.cognitor.tests.CognitorUnitTest.test_token_service
        """
        self.assertIsNotNone(self.srv)
        self.assertIsInstance(self.srv, CognitoTokenService)

    def test_generate_password(self):
        """
        python -m unittest token_service.cognitor.tests.CognitorUnitTest.test_generate_password
        """
        passwd = CognitoTokenService.generate_password()
        self.assertIsNotNone(passwd)
        self.assertEqual(len(passwd), 32)
        # print(passwd)

    def test_list_users(self):
        """
        python -m unittest token_service.cognitor.tests.CognitorUnitTest.test_list_users
        """
        with Stubber(self.mock_client) as stubber:
            # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cognito-idp/client/list_users.html
            response = {
                'Users': [
                    {
                        'Username': 'string',
                        'Attributes': [
                            {
                                'Name': 'string',
                                'Value': 'string'
                            },
                        ],
                        'UserCreateDate': datetime(2015, 1, 1),
                        'UserLastModifiedDate': datetime(2015, 1, 1),
                        'Enabled': True,
                        'UserStatus': 'FORCE_CHANGE_PASSWORD',
                        'MFAOptions': [
                            {
                                'DeliveryMedium': 'EMAIL',
                                'AttributeName': 'string'
                            },
                        ]
                    },
                ],
                'PaginationToken': 'string'
            }
            stubber.add_response('list_users', response)

            d = self.srv.list_users()

            self.assertIn('Users', d.keys())
            self.assertEqual(len(d['Users']), 1)
            print(d['Users'])

    def test_username_exists(self):
        """
        python -m unittest token_service.cognitor.tests.CognitorUnitTest.test_username_exists
        """
        with Stubber(self.mock_client) as stubber:
            stubber.add_client_error('admin_get_user', 'UserNotFoundException')

            b = self.srv.username_exists(username='jajabinks-does-not-exist')

            self.assertFalse(b)
            print(b)

    def test_get_user_not_found(self):
        """
        python -m unittest token_service.cognitor.tests.CognitorUnitTest.test_get_user_not_found
        """
        with Stubber(self.mock_client) as stubber:
            stubber.add_client_error('admin_get_user', 'UserNotFoundException')

            try:
                _ = self.srv.get_user(username='jajabinks-does-not-exist')
            except Exception as e:
                logger.exception(f"THIS ERROR EXCEPTION IS INTENTIONAL FOR TEST. NOT ACTUAL ERROR. \n{e}")
            self.assertRaises(expected_exception=self.srv.client.exceptions.UserNotFoundException)

    def test_register_service_user(self):
        """
        python -m unittest token_service.cognitor.tests.CognitorUnitTest.test_register_service_user
        """
        with Stubber(self.mock_client) as stubber:
            stubber.add_client_error('admin_get_user', 'UserNotFoundException')

            stubber.add_response('sign_up', {
                'UserConfirmed': True,
                'CodeDeliveryDetails': {
                    'Destination': 'string',
                    'DeliveryMedium': 'EMAIL',
                    'AttributeName': 'string'
                },
                'UserSub': 'string'
            })

            stubber.add_response('admin_confirm_sign_up', {})

            self.srv.register_service_user(user_dto=self.jjb_dto)

    def test_get_user(self):
        """
        python -m unittest token_service.cognitor.tests.CognitorUnitTest.test_get_user
        """
        with Stubber(self.mock_client) as stubber:
            stubber.add_response('admin_get_user', {
                'Username': self.jjb_dto.username,
                'UserAttributes': [
                    {
                        'Name': 'string',
                        'Value': 'string'
                    },
                ],
                'UserCreateDate': datetime(2015, 1, 1),
                'UserLastModifiedDate': datetime(2015, 1, 1),
                'Enabled': True,
                'UserStatus': 'CONFIRMED',
                'MFAOptions': [
                    {
                        'DeliveryMedium': 'EMAIL',
                        'AttributeName': 'string'
                    },
                ],
                'PreferredMfaSetting': 'string',
                'UserMFASettingList': [
                    'string',
                ]
            })

            jjb_boto = self.srv.get_user(username=self.jjb_dto.username)
            print(jjb_boto)
            self.assertEqual(jjb_boto['UserStatus'], 'CONFIRMED')

    def test_generate_service_user_tokens(self):
        """
        python -m unittest token_service.cognitor.tests.CognitorUnitTest.test_generate_service_user_tokens
        """
        with Stubber(self.mock_client) as stubber:
            stubber.add_response('initiate_auth', {
                'ChallengeName': 'PASSWORD_VERIFIER',
                'Session': 'this_is_a_session_with_length_of_twenty',
                'ChallengeParameters': {
                    'string': 'string'
                },
                'AuthenticationResult': {
                    'AccessToken': 'string',
                    'ExpiresIn': 123,
                    'TokenType': 'string',
                    'RefreshToken': 'string',
                    'IdToken': 'string',
                    'NewDeviceMetadata': {
                        'DeviceKey': 'string',
                        'DeviceGroupKey': 'string'
                    }
                }
            })

            jjb_tokens = self.srv.generate_service_user_tokens(user_dto=self.jjb_dto)
            print(jjb_tokens)
            self.assertIn('id_token', jjb_tokens.keys())

    def test_rotate_service_user_password(self):
        """
        python -m unittest token_service.cognitor.tests.CognitorUnitTest.test_rotate_service_user_password
        """
        with Stubber(self.mock_client) as stubber:
            stubber.add_response('admin_get_user', {'Username': self.jjb_dto.username, })
            stubber.add_response('admin_set_user_password', {})

            self.srv.rotate_service_user_password(user_dto=self.jjb_dto)

    def test_cleanup_service_user(self):
        """
        python -m unittest token_service.cognitor.tests.CognitorUnitTest.test_cleanup_service_user
        """
        with Stubber(self.mock_client) as stubber:
            stubber.add_response('admin_disable_user', {})
            stubber.add_response('admin_delete_user', {})
            stubber.add_client_error('admin_get_user', 'UserNotFoundException')

            self.srv.disable_user(username=self.jjb_dto.username)  # disable jjb
            self.srv.delete_user(username=self.jjb_dto.username)  # delete jjb
            self.assertFalse(self.srv.username_exists(username=self.jjb_dto.username))  # assert that jjb mocker gone
