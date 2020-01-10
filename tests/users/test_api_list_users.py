import unittest
from flask import json
from flask_restplus import marshal
import urllib.parse

from app import messages
from app.api.models.user import public_user_api_model
from app.database.models.user import UserModel
from app.database.sqlalchemy_extension import db
from tests.base_test_case import BaseTestCase
from tests.test_utils import get_test_request_header
from tests.test_data import user1, user2, user3


class TestListUsersApi(BaseTestCase):
    def setUp(self):
        super(TestListUsersApi, self).setUp()

        self.verified_user = UserModel(
            name=user1['name'],
            email=user1['email'],
            username=user1['username'],
            password=user1['password'],
            terms_and_conditions_checked=user1['terms_and_conditions_checked']
        )
        self.other_user = UserModel(
            name=user2['name'],
            email=user2['email'],
            username=user2['username'],
            password=user2['password'],
            terms_and_conditions_checked=user2['terms_and_conditions_checked']
        )
        # This user's name contains special characters to properly test the `search` param working.
        self.other_user2 = UserModel(
            name=user3['name'],
            email=user3['email'],
            username=user3['username'],
            password=user3['password'],
            terms_and_conditions_checked=user3['terms_and_conditions_checked']
        )

        self.verified_user.is_email_verified = True
        db.session.add(self.verified_user)
        db.session.add(self.other_user)
        db.session.add(self.other_user2)
        db.session.commit()

    def test_list_users_api_resource_non_auth(self):
        expected_response = messages.AUTHORISATION_TOKEN_IS_MISSING
        actual_response = self.client.get('/users', follow_redirects=True)

        self.assertEqual(401, actual_response.status_code)
        self.assertDictEqual(expected_response, json.loads(actual_response.data))

    def test_list_users_api_resource_auth(self):
        auth_header = get_test_request_header(self.admin_user.id)
        expected_response = [marshal(self.verified_user, public_user_api_model), marshal(self.other_user, public_user_api_model), marshal(self.other_user2, public_user_api_model)]
        actual_response = self.client.get('/users', follow_redirects=True, headers=auth_header)

        self.assertEqual(200, actual_response.status_code)
        self.assertEqual(expected_response, json.loads(actual_response.data))

    def test_list_users_api_resource_verified_users(self):
        auth_header = get_test_request_header(self.admin_user.id)
        expected_response = [marshal(self.verified_user, public_user_api_model)]
        actual_response = self.client.get('/users/verified', follow_redirects=True, headers=auth_header)

        self.assertEqual(200, actual_response.status_code)
        self.assertEqual(expected_response, json.loads(actual_response.data))

    """
        This case tests the functioning of the `search` param in the `/users` API endpoint.
        If the name entered in the search param is found in the users list,
        then the user whose name matches with the search param is returned,
        else a null object is returned.
    """
    def test_list_users_api_resource_user_search_param(self):
        auth_header = get_test_request_header(self.admin_user.id)
        expected_response = [marshal(self.other_user2, public_user_api_model)]
        # Encoding the search param
        search_name = urllib.parse.quote(self.other_user2.name)
        actual_response = self.client.get('/users?search=%s' % search_name, follow_redirects=True, headers=auth_header)
        self.assertEqual(200, actual_response.status_code)
        self.assertEqual(expected_response, json.loads(actual_response.data))

if __name__ == "__main__":
    unittest.main()
