import json
import os
import StringIO
import tempfile

from django.conf import settings
from django.contrib.auth.models import User
from django.core import management, mail

import requests
from mock import ANY, patch
from nose.tools import eq_
from test_utils import TestCase

from remo.profiles.management.commands.fetch_emails_from_wiki import Command


class CreateUserTest(TestCase):
    """Tests for create_user management command."""

    def setUp(self):
        """Setup tests.

        Create an actual file in the filesystem with valid and
        invalid emails. Delete the file on exit.

        """
        # check if actual email sending is enabled and if yes do not run
        if ((settings.EMAIL_BACKEND !=
             'django.core.mail.backends.locmem.EmailBackend')):
            raise ValueError('Please change local.py to avoid '
                             'sending testing emails')

        # create a temporaty file with emails
        self.TEST_EMAILS = ['foo@example.com', 'bar@example.com',
                            'bogusemail.com', 'foo@example.com']
        self.NUMBER_VALID_EMAILS = 2
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)

        self.number_of_users_in_db = User.objects.count()

        for email in self.TEST_EMAILS:
            self.temp_file.write(email)
            self.temp_file.write('\n')

        self.temp_file.close()

    def test_command_without_input_file(self):
        """Test that command exits with SystemExit exception when called
        without an input file.

        """
        args = []
        opts = {}
        self.assertRaises(SystemExit, management.call_command,
                          'create_users', *args, **opts)

    def test_command_input_file_no_email(self):
        """Test that users get successfully created and no email is sent."""
        args = [self.temp_file.name]
        opts = {'email': False}
        management.call_command('create_users', *args, **opts)
        eq_(len(mail.outbox), 0)
        eq_(User.objects.count(),
            self.NUMBER_VALID_EMAILS + self.number_of_users_in_db)

    def test_command_input_file_send_email(self):
        """Test that users get successfully created and emails are sent."""
        args = [self.temp_file.name]
        opts = {'email': True}
        management.call_command('create_users', *args, **opts)
        eq_(len(mail.outbox), self.NUMBER_VALID_EMAILS)
        eq_(User.objects.count(),
            self.NUMBER_VALID_EMAILS + self.number_of_users_in_db)

    def tearDown(self):
        """Cleanup Tests.

        Delete the temporary file with emails used during the tests.

        """
        os.unlink(self.temp_file.name)


class FetchEmailsFromWikiTest(TestCase):
    """Tests for fetch_emails_from_wiki management command."""

    @patch('requests.get')
    def test_command_with_connection_error(self, fake_get):
        """Test that command exits with SystemExit exception on connection
        error.

        """
        fake_get.side_effect = requests.ConnectionError()
        with self.assertRaises(SystemExit):
            management.call_command('fetch_emails_from_wiki')
        fake_get.assert_called_with(ANY)

    @patch('requests.get')
    def test_command_with_invalid_code(self, fake_get):
        """Test that command exits with SystemExit exception on 404 error."""
        request = requests.Request()
        request.status_code = 404
        request.text = 'foo'
        fake_get.return_value = request
        with self.assertRaises(SystemExit):
            management.call_command('fetch_emails_from_wiki')
        fake_get.assert_called_with(ANY)

    @patch('requests.get')
    def test_command_with_bogus_data(self, fake_get):
        """Test that command exits with SystemExit exception on json decode
        error.

        """
        request = requests.Request()
        request.status_code = 200
        request.text = 'foo'
        fake_get.return_value = request
        with self.assertRaises(SystemExit):
            management.call_command('fetch_emails_from_wiki')
        fake_get.assert_called_with(ANY)

    @patch('remo.profiles.management.commands.fetch_emails_from_wiki.requests')
    def test_command_with_valid_data(self, fake_requests):
        """Test that command successfully fetches data and prints out
        emails.

        """
        request = requests.Request()
        request.status_code = 200
        request.text = json.dumps(
            {'ask':
             {'query': {},
              'results': {
                  'items':
                  [{'properties': {'bugzillamail': 'foo@example.com'},
                    'uri': ('https:\/\/wiki.mozilla.org\/index.php?'
                            'title=User:fooexample')},
                   {'properties': {'bugzillamail': 'test@example.com'},
                    'uri': ('https:\/\/wiki.mozilla.org\/index.php?'
                            'title=User:testexample')},
                   {'properties': {'bugzillamail': 'testexample.com'},
                    'uri': ('https:\/\/wiki.mozilla.org\/index.php?'
                            'title=User:bogus')}]}}})

        fake_requests.get.return_value = request

        output = StringIO.StringIO()
        cmd_obj = Command()
        cmd_obj.stdout = output
        cmd_obj.handle()

        # check each line of the output to ensure parsing
        lines = output.getvalue().split('\n')
        eq_(len(lines), 3)
        eq_(lines[0], 'foo@example.com')
        eq_(lines[1], 'test@example.com')
        eq_(lines[2], '')


class CronjobsTest(TestCase):
    """Tests for cronjobs management command."""

    def test_new_reps_reminder(self):
        """Test monthly email reminder for new reps."""

        args = ['new_reps_reminder']
        management.call_command('cron', *args)
        eq_(len(mail.outbox), 1)

        reminder = mail.outbox[0]
        eq_(reminder.from_email, settings.FROM_EMAIL)
        eq_(reminder.to, [settings.REPS_MENTORS_LIST])
