import happyforms

from django import forms
from django.contrib import messages

from remo.base.tasks import send_remo_mail
from remo.profiles.models import FunctionalArea, UserProfile


class BaseEmailUsersFrom(happyforms.Form):
    """Base form to send email to multiple users."""
    subject = forms.CharField(label='', widget=(
        forms.TextInput(attrs={'placeholder': 'Subject',
                               'required': 'required',
                               'class': 'input-text big'})))
    body = forms.CharField(label='', widget=(
        forms.Textarea(attrs={'placeholder': 'Body of email',
                              'required': 'required',
                              'class': 'flat long'})))


class EmailUsersForm(BaseEmailUsersFrom):
    """Generic form to send email to multiple users."""

    def __init__(self, users, *args, **kwargs):
        """Initialize form.

        Dynamically set fields for the recipients of the mail.
        """
        super(EmailUsersForm, self).__init__(*args, **kwargs)
        for user in users:
            # Insert method is used to override the order of form fields
            form_widget = forms.CheckboxInput(
                attrs={'class': 'input-text-big'})
            self.fields.insert(0, str(user.id),
                               forms.BooleanField(
                                   label=user,
                                   initial=True,
                                   required=False,
                                   widget=form_widget))

    def send_mail(self, request):
        """Send mail to recipients list."""
        recipients_list = []
        for field in self.fields:
            if (isinstance(self.fields[field], forms.BooleanField) and
                    self.cleaned_data[field]):
                recipients_list.append(long(field))

        if recipients_list:
            from_email = '%s <%s>' % (request.user.get_full_name(),
                                      request.user.email)
            send_remo_mail.delay(sender=from_email,
                                 recipients_list=recipients_list,
                                 subject=self.cleaned_data['subject'],
                                 message=self.cleaned_data['body'])
            messages.success(request, 'Email sent successfully.')
        else:
            messages.error(request, ('Email not sent. Please select at '
                                     'least one recipient.'))


class EmailRepsForm(BaseEmailUsersFrom):
    """Generic form to send email to multiple users."""

    functional_area = forms.ModelChoiceField(
        queryset=FunctionalArea.active_objects.all(), empty_label=None,
        widget=forms.HiddenInput())

    def send_email(self, request, users):
        """Send mail to recipients list."""
        recipients = users.values_list('id', flat=True)

        if recipients:
            from_email = '%s <%s>' % (request.user.get_full_name(),
                                      request.user.email)
            send_remo_mail.delay(sender=from_email,
                                 recipients_list=recipients,
                                 subject=self.cleaned_data['subject'],
                                 message=self.cleaned_data['body'])
            messages.success(request, 'Email sent successfully.')
        else:
            messages.error(request, 'Email not sent. An error occured.')


class EditSettingsForm(happyforms.ModelForm):
    """Form to edit user settings regarding mail preferences."""
    receive_email_on_add_comment = forms.BooleanField(
        required=False, initial=True,
        label=('Receive email when a user comments on a report.'))
    receive_email_on_add_event_comment = forms.BooleanField(
        required=False, initial=True,
        label=('Receive email when a user comments on an event.'))

    class Meta:
        model = UserProfile
        fields = ['receive_email_on_add_comment',
                  'receive_email_on_add_event_comment']


class TrackFunctionalAreasForm(happyforms.ModelForm):
    """Form for tracking interests in functional areas for Mozillians."""

    class Meta:
        model = UserProfile
        fields = ['tracked_functional_areas']
