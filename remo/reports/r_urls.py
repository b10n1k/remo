from django.conf.urls.defaults import patterns, url

OPTIONAL_PARAMETER_REGEX = '(?:/(?P<day>\d+)/(?P<id>\d+))?'

urlpatterns = patterns(
    'remo.reports.views',
    url(r'^(?P<year>\d+)/(?P<month>\w+)%s/$' % OPTIONAL_PARAMETER_REGEX,
        'view_ng_report', name='reports_ng_view_report'),
    url(r'^(?P<year>\d+)/(?P<month>\w+)/(?P<day>\d+)/(?P<id>\d+)/edit/$',
        'edit_ng_report', name='reports_ng_edit_report'),
    url(r'^(?P<year>\d+)/(?P<month>\w+)/(?P<day>\d+)/(?P<id>\d+)/delete/$',
        'delete_ng_report', name='reports_ng_delete_report'),
    url((r'^(?P<year>\d+)/(?P<month>\w+)/(?P<day>\d+)/(?P<id>\d+)'
        '/comment/(?P<comment_id>\d+)/delete/$'),
        'delete_ng_report_comment', name='reports_ng_delete_report_comment'),
)
