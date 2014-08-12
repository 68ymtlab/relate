# -*- coding: utf-8 -*-

from __future__ import division

__copyright__ = "Copyright (C) 2014 Andreas Kloeckner"

__license__ = """
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

from django.shortcuts import (  # noqa
        render, get_object_or_404, redirect)
from django.contrib import messages  # noqa
from django.core.exceptions import PermissionDenied
import django.forms as forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from course.auth import get_role_and_participation
from course.models import (Course, participation_role,
        InstantMessage)

from course.content import (
        get_course_repo, get_course_desc, get_active_commit_sha)

import sleekxmpp

import threading


# {{{ instant message

class InstantMessageForm(forms.Form):
    message = forms.CharField(required=True)

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-lg-2"
        self.helper.field_class = "col-lg-8"

        self.helper.add_input(
                Submit("submit", "Send", css_class="col-lg-offset-2"))

        super(InstantMessageForm, self).__init__(*args, **kwargs)


_xmpp_connections = {}
_disconnectors = []


class CourseXMPP(sleekxmpp.ClientXMPP):
    def __init__(self, jid, password, recipient_jid):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)
        self.recipient_jid = recipient_jid

        self.add_event_handler("session_start", self.start)
        self.add_event_handler("changed_status", self.wait_for_presences)

        self.received = set()

        self.presences_received = threading.Event()

    def start(self, event):
        self.send_presence()
        self.get_roster()

    def is_recipient_online(self):
        groups = self.client_roster.groups()
        for group in groups:
            for jid in groups[group]:
                if jid != self.recipient_jid:
                    continue

                connections = self.client_roster.presence(jid)
                for res, pres in connections.items():
                    return True

        return False

    def wait_for_presences(self, pres):
        """
        Track how many roster entries have received presence updates.
        """
        self.received.add(pres['from'].bare)
        if len(self.received) >= len(self.client_roster.keys()):
            self.presences_received.set()
        else:
            self.presences_received.clear()


class Disconnector(object):
    def __init__(self, xmpp, course):
        self.timer = None
        self.xmpp = xmpp
        self.course = course

        self.timer = threading.Timer(60, self)
        self.timer.start()

    def __call__(self):
        # print "EXPIRING XMPP", self.course.pk
        del _xmpp_connections[self.course.pk]
        self.xmpp.disconnect(wait=True)
        _disconnectors.remove(self)


def get_xmpp_connection(course):
    try:
        return _xmpp_connections[course.pk]
    except KeyError:
        xmpp = CourseXMPP(
                course.course_xmpp_id,
                course.course_xmpp_password,
                course.recipient_xmpp_id)
        if xmpp.connect():
            xmpp.process()
        else:
            raise RuntimeError("unable to connect")

        _xmpp_connections[course.pk] = xmpp

        xmpp.presences_received.wait(5)
        xmpp.is_recipient_online()

        _disconnectors.append(Disconnector(xmpp, course))

        return xmpp


def send_instant_message(request, course_identifier):
    course = get_object_or_404(Course, identifier=course_identifier)

    role, participation = get_role_and_participation(request, course)
    if role not in [
            participation_role.student,
            participation_role.teaching_assistant,
            participation_role.instructor]:
        raise PermissionDenied("only enrolled folks may do that")

    if not course.course_xmpp_id:
        messages.add_message(request, messages.ERROR,
                "Instant messaging is not enabled for this course.")

        return redirect("course.views.course_page", course_identifier)

    repo = get_course_repo(course)
    commit_sha = get_active_commit_sha(course, participation)
    course_desc = get_course_desc(repo, course, commit_sha)

    xmpp = get_xmpp_connection(course)
    if xmpp.is_recipient_online():
        form_text = "Recipient is <span class=\"label label-success\">Online</span>."
    else:
        form_text = "Recipient is <span class=\"label label-danger\">Offline</span>."
    form_text = "<div class=\"well\">%s</div>" % form_text

    if request.method == "POST":
        form = InstantMessageForm(request.POST, request.FILES)
        if form.is_valid():
            msg = InstantMessage()
            msg.participation = participation
            msg.text = form.cleaned_data["message"]
            msg.save()

            try:
                if not course.recipient_xmpp_id:
                    raise RuntimeError("no recipient XMPP ID")

                if not course.course_xmpp_password:
                    raise RuntimeError("no XMPP password")

                xmpp.send_message(
                        mto=course.recipient_xmpp_id,
                        mbody=form.cleaned_data["message"],
                        mtype='chat')

            except Exception:
                from traceback import print_exc
                print_exc()

                messages.add_message(request, messages.ERROR,
                        "An error occurred while sending the message. Sorry.")
            else:
                messages.add_message(request, messages.SUCCESS,
                        "Message sent.")
                form = InstantMessageForm()

    else:
        form = InstantMessageForm()

    return render(request, "course/generic-course-form.html", {
        "participation": participation,
        "form": form,
        "form_text": form_text,
        "role": role,
        "participation_role": participation_role,
        "form_description": "Send instant message",
        "course": course,
        "course_desc": course_desc,
    })

# }}}

# vim: foldmethod=marker
