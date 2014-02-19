from django.conf.urls.defaults import patterns, url
from django.core.urlresolvers import reverse_lazy

from remo.base.views import (BaseCreateView, BaseDeleteView, BaseListView,
                             BaseUpdateView)
from remo.profiles.forms import FunctionalAreaForm
from remo.profiles.models import FunctionalArea
from remo.reports.forms import ActivityForm, CampaignForm
from remo.reports.models import Activity, Campaign


urlpatterns = patterns(
    '',
    url('^activities/$',
        BaseListView.as_view(
            model=Activity, create_object_url=reverse_lazy('create_activity')),
        name='list_activities'),
    url('^activities/(?P<pk>\d+)/delete/$',
        BaseDeleteView.as_view(
            model=Activity, success_url=reverse_lazy('list_activities')),
        name='delete_activity'),
    url('^activities/new/$',
        BaseCreateView.as_view(
            model=Activity, form_class=ActivityForm,
            success_url=reverse_lazy('list_activities')),
        name='create_activity'),
    url('^activities/(?P<pk>\d+)/edit/$',
        BaseUpdateView.as_view(
            model=Activity, form_class=ActivityForm,
            success_url=reverse_lazy('list_activities')),
        name='edit_activity'),
    url('^campaigns/$',
        BaseListView.as_view(
            model=Campaign, create_object_url=reverse_lazy('create_campaign')),
        name='list_campaigns'),
    url('^campaigns/(?P<pk>\d+)/delete/$',
        BaseDeleteView.as_view(
            model=Campaign, success_url=reverse_lazy('list_campaigns')),
        name='delete_campaign'),
    url('^campaigns/new/$',
        BaseCreateView.as_view(
            model=Campaign, form_class=CampaignForm,
            success_url=reverse_lazy('list_campaigns')),
        name='create_campaign'),
    url('^campaigns/(?P<pk>\d+)/edit/$',
        BaseUpdateView.as_view(
            model=Campaign, form_class=CampaignForm,
            success_url=reverse_lazy('list_campaigns')),
        name='edit_campaign'),
    url('^functional_areas/$',
        BaseListView.as_view(
            model=FunctionalArea,
            create_object_url=reverse_lazy('create_functional_area')),
        name='list_functional_areas'),
    url('^functional_areas/(?P<pk>\d+)/delete/$',
        BaseDeleteView.as_view(
            model=FunctionalArea,
            success_url=reverse_lazy('list_functional_areas')),
        name='delete_functional_area'),
    url('^functional_areas/new/$',
        BaseCreateView.as_view(
            model=FunctionalArea, form_class=FunctionalAreaForm,
            success_url=reverse_lazy('list_functional_areas')),
        name='create_functional_area'),
    url('^functional_areas/(?P<pk>\d+)/edit/$',
        BaseUpdateView.as_view(
            model=FunctionalArea, form_class=FunctionalAreaForm,
            success_url=reverse_lazy('list_functional_areas')),
        name='edit_functional_area'),
)
