import datetime

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core import mail
from django.utils.timezone import now

from mock import patch
from nose.tools import eq_, ok_
from test_utils import TestCase

from remo.profiles.tests import UserFactory
from remo.remozilla.tests import BugFactory
from remo.voting.models import Poll


class VotingMailNotificationTest(TestCase):
    """Tests related to Voting Models."""
    fixtures = ['demo_users.json']

    def setUp(self):
        """Initial data for the tests."""
        self.user = User.objects.get(username='admin')
        self.group = Group.objects.get(name='Admin')
        self._now = now()
        self.now = self._now.replace(microsecond=0)
        self.start = self.now
        self.end = self.now + datetime.timedelta(days=5)
        self.voting = Poll(name='poll', start=self.start, end=self.end,
                           valid_groups=self.group, created_by=self.user)
        self.voting.save()

    def test_send_email_on_save_poll(self):
        """Test sending emails when a new voting is added."""
        recipients = map(lambda x: '%s' % x.email,
                         User.objects.filter(groups=self.group))
        eq_(len(mail.outbox), 2)
        ok_(mail.outbox[0].to[0] in recipients)
        ok_(mail.outbox[1].to[0] in recipients)

    @patch('remo.voting.models.celery_control.revoke')
    def test_send_email_on_edit_poll(self, fake_revoke):
        """Test sending emails when the poll is edited."""
        Poll.objects.filter(pk=self.voting.id).update(task_start_id='1234',
                                                      task_end_id='1234')
        poll = Poll.objects.get(pk=self.voting.id)
        poll.name = 'Edit Voting'
        if not settings.CELERY_ALWAYS_EAGER:
            fake_revoke.return_value = True
        poll.save()
        eq_(len(mail.outbox), 3)

    def test_send_email_to_council_members(self):
        """Test send emails to Council Members if an automated poll is created.

        """
        automated_poll = Poll(name='automated_poll', start=self.start,
                              end=self.end, valid_groups=self.group,
                              created_by=self.user, automated_poll=True)
        automated_poll.save()
        eq_(len(mail.outbox), 4)
        for email in mail.outbox:
            if settings.REPS_COUNCIL_ALIAS in email.to:
                break
        else:
            raise Exception('No email sent to REPS_COUNCIL_ALIAS')


class AutomatedRadioPollTest(TestCase):
    """Tests the automatic creation of new Radio polls."""
    fixtures = ['demo_users.json']

    def test_automated_radio_poll_valid_bug(self):
        """Test the creation of an automated radio poll."""
        UserFactory.create(username='remobot')
        bug = BugFactory.create(council_vote_requested=True,
                                component='Budget Requests')
        poll = Poll.objects.get(bug=bug)
        eq_(poll.bug.bug_id, bug.bug_id)
        eq_(poll.description, bug.first_comment)
        eq_(poll.name, bug.summary)

    def test_automated_radio_poll_no_auto_bug(self):
        """Test the creation of an automated radio
        poll with a non budget/swag bug.

        """
        BugFactory.create()
        eq_(Poll.objects.filter(automated_poll=True).count(), 0)

    def test_automated_radio_poll_already_exists(self):
        """Test that a radio poll is not created
        if the bug already exists.

        """
        UserFactory.create(username='remobot')
        bug = BugFactory.create(council_vote_requested=True,
                                component='Budget Requests')
        bug.first_comment = 'My first comment.'
        bug.save()
        eq_(Poll.objects.filter(automated_poll=True).count(), 1)
