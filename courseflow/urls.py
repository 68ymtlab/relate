from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns('',
    url(r'^login/by-email/$',
        'course.views.sign_in_by_email'),
    url(r'^logout/$',
        'django.contrib.auth.views.logout',
        {'template_name': 'base.html'}),

    url(r'^$', 'course.views.home', name='home'),
    url(r"^course"
        "/(?P<course_identifier>[-a-zA-Z0-9]+)"
        "/$",
        "course.views.course_page",),
    url(r"^course"
        "/(?P<course_identifier>[-a-zA-Z0-9]+)"
        "/enroll/$",
        "course.views.enroll",),
    url(r"^course"
        "/(?P<course_identifier>[-a-zA-Z0-9]+)"
        "/pull/$",
        "course.views.pull_course_updates",),
    url(r"^course"
        "/(?P<course_identifier>[-a-zA-Z0-9]+)"
        "/update/$",
        "course.views.update_course",),
    url(r"^course"
         "/(?P<course_identifier>[-a-zA-Z0-9]+)"
         "/flow"
         "/(?P<flow_identifier>[-_a-zA-Z0-9]+)"
         "/start"
         "/$",
         "course.views.start_flow",),
    url(r"^course"
        "/(?P<course_identifier>[-a-zA-Z0-9]+)"
        "/flow"
        "/(?P<flow_identifier>[-_a-zA-Z0-9]+)"
        "/group"
        "/(?P<group_identifier>[-_a-zA-Z0-9]+)"
        "/(?P<page_identifier>[-_a-zA-Z0-9]+)"
        "/$",
        "course.views.view_flow_page",),

    url(r'^admin/', include(admin.site.urls)),
)
