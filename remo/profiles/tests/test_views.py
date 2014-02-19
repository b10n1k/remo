# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.encoding import iri_to_uri

import mock
from nose.tools import eq_, ok_
from pyquery import PyQuery as pq
from test_utils import TestCase

from remo.base.tests import requires_permission, requires_login
from remo.profiles.tests import FunctionalAreaFactory, UserFactory


class ViewsTest(TestCase):
    """Tests related to Profiles Views."""

    def setUp(self):
        """Setup tests."""
        self.mentor = UserFactory.create(groups=['Rep', 'Mentor'],
                                         userprofile__initial_council=True)
        self.rep = UserFactory.create(groups=['Rep'],
                                      userprofile__mentor=self.mentor)
        self.area = FunctionalAreaFactory.create()
        profile = self.rep.userprofile

        self.data = {'display_name': profile.display_name,
                     'first_name': self.rep.first_name,
                     'email': self.rep.email,
                     'last_name': self.rep.last_name,
                     'local_name': profile.local_name,
                     'private_email': self.rep.email,
                     'twitter_account': profile.twitter_account,
                     'city': profile.city,
                     'region': profile.region,
                     'country': profile.country,
                     'lon': profile.lat,
                     'lat': profile.lon,
                     'mozillians_profile_url': profile.mozillians_profile_url,
                     'wiki_profile_url': profile.wiki_profile_url,
                     'jabber_id': u'foo@jabber.org',
                     'irc_name': profile.irc_name,
                     'linkedin_url': u'http://www.linkedin.com/',
                     'facebook_url': u'http://www.facebook.com/',
                     'diaspora_url': u'https://joindiaspora.com/',
                     'personal_website_url': u'http://www.example.com/',
                     'personal_blog_feed': u'http://example.com/',
                     'bio': u'This is my bio.',
                     'date_joined_program': '2011-07-01',
                     'mentor': profile.mentor.id,
                     'functional_areas': self.area.id}

        display_name = {'display_name': profile.display_name}

        self.user_url = reverse('profiles_view_profile', kwargs=display_name)
        self.user_edit_url = reverse('profiles_edit', kwargs=display_name)
        self.user_delete_url = reverse('profiles_delete', kwargs=display_name)

    def test_view_my_profile_page(self):
        """Get my profile page."""
        self.client.login(username=self.mentor.username, password='passwd')
        response = self.client.get(reverse('profiles_view_my_profile'))
        self.assertTemplateUsed(response, 'profiles_view.html')

    def test_view_invite_page(self):
        """Get invite page."""
        self.client.login(username=self.mentor.username, password='passwd')
        response = self.client.get(reverse('profiles_invite'))
        self.assertTemplateUsed(response, 'profiles_invite.html')

    def test_view_list_profiles_page(self):
        """Get list profiles page."""
        response = self.client.get(reverse('profiles_list_profiles'))
        self.assertTemplateUsed(response, 'profiles_people.html')

    def test_view_profile_page(self):
        """Get profile page."""
        response = self.client.get(self.user_url)
        self.assertTemplateUsed(response, 'profiles_view.html')

    def test_view_edit_profile_page(self):
        """Get edit profile page."""
        self.client.login(username=self.rep.username, password='passwd')
        response = self.client.get(self.user_edit_url)
        self.assertTemplateUsed(response, 'profiles_edit.html')

    def test_view_delete_profile_page(self):
        """Get delete profile page."""
        admin = UserFactory.create(groups=['Admin'])
        self.client.login(username=admin.username, password='passwd')
        response = self.client.get(self.user_delete_url, follow=True)
        self.assertTemplateUsed(response, 'main.html')

    def test_invite_user(self):
        """Test that user is invited."""
        self.client.login(username=self.mentor.username, password='passwd')
        self.client.post(reverse('profiles_invite'),
                         {'email': 'foobar@example.com'})

        u = User.objects.get(email='foobar@example.com')
        eq_(u.userprofile.added_by, self.mentor)
        ok_(u.groups.filter(name='Rep').exists())

    def test_edit_profile_permissions_owner(self):
        """Test owner permissions to edit profiles."""
        self.client.login(username=self.rep.username, password='passwd')
        response = self.client.get(self.user_edit_url, follow=True)
        self.assertTemplateUsed(response, 'profiles_edit.html')

    def test_edit_profile_permissions_admin(self):
        """Test admin permission to edit profile."""
        admin = UserFactory.create(groups=['Admin'])
        self.client.login(username=admin.username, password='passwd')
        response = self.client.get(self.user_edit_url, follow=True)
        self.assertTemplateUsed(response, 'profiles_edit.html')

    @requires_permission()
    def test_edit_profile_no_permissions(self):
        """Test user edit other user profile without permission."""
        self.client.login(username=self.mentor.username, password='passwd')
        self.client.get(self.user_edit_url, follow=True)

    def test_edit_profile_redirect_admin(self):
        """Test that after edit profile redirection is correct."""
        admin = UserFactory.create(groups=['Admin'])
        self.client.login(username=admin.username, password='passwd')
        response = self.client.post(self.user_edit_url, self.data, follow=True)
        eq_(response.request['PATH_INFO'], self.user_url)

    def test_edit_owner_profile_redirect(self):
        """Test that after edit profile redirection is correct."""
        self.client.login(username=self.rep.username, password='passwd')
        response = self.client.post(self.user_edit_url, self.data, follow=True)
        eq_(response.request['PATH_INFO'], reverse('profiles_view_my_profile'))

    def test_delete_own_profile(self):
        """Test owner can't delete his profile."""
        self.client.login(username=self.rep.username, password='passwd')
        response = self.client.post(self.user_delete_url, follow=True)
        self.assertTemplateUsed(response, 'main.html')
        ok_(User.objects.filter(pk=self.rep.id).exists())

    @requires_permission()
    def test_delete_user_delete_profile_no_perms(self):
        """Test user can't delete profile without permissions."""
        user = UserFactory.create(groups=['Rep'])
        self.client.login(username=user.username, password='passwd')
        self.client.post(self.user_delete_url, follow=True)
        ok_(User.objects.filter(pk=self.rep.id).exists())

    def test_delete_profile_admin(self):
        """Test admin can delete profile."""
        admin = UserFactory.create(groups=['Admin'])
        self.client.login(username=admin.username, password='passwd')
        response = self.client.post(self.user_delete_url, {'delete': 'true'},
                                    follow=True)
        self.assertTemplateUsed(response, 'main.html')
        ok_(not User.objects.filter(pk=self.rep.id).exists())

    def test_profiles_me(self):
        """Test that user gets own profile rendered."""
        # user gets own profile page rendered
        self.client.login(username=self.rep.username, password='passwd')
        response = self.client.get(reverse('profiles_view_my_profile'),
                                   follow=True)
        self.assertTemplateUsed(response, 'profiles_view.html')

    @requires_login()
    def test_profiles_me_anonymous(self):
        # anonymous user get message to login first
        self.client.get(reverse('profiles_view_my_profile'), follow=True)

    def test_incomplete_profile(self):
        """Test user redirection when profile is incomplete"""
        # First name is empty to keep registration_complete=False
        user = UserFactory.create(groups=['Rep'], first_name='',
                                  userprofile__registration_complete=False)
        self.client.login(username=user.username, password='passwd')
        response = self.client.get(reverse('profiles_view_my_profile'),
                                   follow=True)
        self.assertTemplateUsed(response, 'profiles_edit.html')

    def test_case_insensitive_profile_url(self):
        """Test the display_name is case insensitive in profile urls."""
        self.client.login(username=self.rep.username, password='passwd')
        name = self.rep.userprofile.display_name.upper()
        response = self.client.get(reverse('profiles_view_profile',
                                           kwargs={'display_name': name}),
                                   follow=True)
        self.assertTemplateUsed(response, 'profiles_view.html')

        response = self.client.get(reverse('profiles_edit',
                                           kwargs={'display_name': name}),
                                   follow=True)
        self.assertTemplateUsed(response, 'profiles_edit.html')

    def test_number_of_reps_visibility_unauthed(self):
        """Test visibility of number of reps based on authentication status."""
        response = self.client.get(reverse('profiles_list_profiles'),
                                   follow=True)
        d = pq(response.content)
        eq_(len(d('#profiles-number-of-reps')), 0)

    def test_number_of_reps_visibility_authenticated(self):
        """Test visibility of number of reps based on authentication status."""
        self.client.login(username=self.rep.username, password='passwd')
        response = self.client.get(reverse('profiles_list_profiles'),
                                   follow=True)
        d = pq(response.content)
        eq_(len(d('#profiles-number-of-reps')), 1)

    def test_view_incomplete_profile_page_unauthed(self):
        """Test permission to view incomplete profile page unauthenticated."""
        user = UserFactory.create(groups=['Rep'], first_name='',
                                  userprofile__registration_complete=False)
        name = user.userprofile.display_name
        url = reverse('profiles_view_profile',
                      kwargs={'display_name': name})

        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, '404.html',
                                'Anonymous can view the page')

    def test_view_incomplete_profile_page_authenticated(self):
        """Test view incomplete profile page without permissions."""
        user = UserFactory.create(groups=['Rep'], first_name='',
                                  userprofile__registration_complete=False)
        name = user.userprofile.display_name
        url = reverse('profiles_view_profile',
                      kwargs={'display_name': name})
        self.client.login(username=self.rep.username, password='passwd')
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, '404.html',
                                'Rep without permission can view the page')

    def test_view_incomplete_profile_page_admin(self):
        """Test permission to view incomplete profile page as admin."""
        admin = UserFactory.create(groups=['Admin'])
        user = UserFactory.create(groups=['Rep'], first_name='',
                                  userprofile__registration_complete=False)
        name = user.userprofile.display_name
        url = reverse('profiles_view_profile',
                      kwargs={'display_name': name})
        self.client.login(username=admin.username, password='passwd')
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, 'profiles_view.html',
                                'Admin can\'t view the page')

    @mock.patch('remo.profiles.views.iri_to_uri', wraps=iri_to_uri)
    def test_view_redirect_list_profiles(self, mocked_uri):
        """Test redirect to profiles list."""
        profiles_url = '/people/Paris & Orléans'
        response = self.client.get(profiles_url, follow=True)
        mocked_uri.assert_called_once_with(u'/Paris & Orléans')
        expected_url = '/people/#/Paris%20&%20Orl%C3%A9ans'
        self.assertRedirects(response, expected_url=expected_url,
                             status_code=301, target_status_code=200)
        self.assertTemplateUsed(response, 'profiles_people.html')

    def test_functional_areas_type(self):
        """Test that functional area type is integer."""
        self.client.login(username=self.rep.username, password='passwd')

        # Post form with invalid data
        self.data['wiki_profile_url'] = 'www.example.com'
        response = self.client.post(self.user_edit_url, self.data, follow=True)

        eq_(response.context['functional_areas'], [self.area.id])
