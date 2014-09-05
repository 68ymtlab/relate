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
        redirect, get_object_or_404)
from course.utils import course_view, render_course_page
from django.contrib import messages  # noqa
from django.core.exceptions import PermissionDenied

from course.models import (
        Participation, participation_role, participation_status,
        GradingOpportunity, GradeChange, GradeStateMachine,
        grade_state_change_types)


# {{{ student grade book

@course_view
def view_my_grades(pctx):
    messages.add_message(pctx.request, messages.ERROR,
            "Grade viewing is not yet implemented. (Sorry!) It will be "
            "once you start accumulating a sufficient number of grades.")

    return redirect("course.views.course_page", pctx.course.identifier)

# }}}


# {{{ teacher grade book

class GradeInfo(object):
    def __init__(self, participation, opportunity, grade_state_machine):
        self.participation = participation
        self.opportunity = opportunity
        self.grade_state_machine = grade_state_machine


@course_view
def view_gradebook(pctx):
    if pctx.role not in [
            participation_role.instructor,
            participation_role.teaching_assistant]:
        raise PermissionDenied("must be instructor or TA to view grades")

    grading_opps = list((GradingOpportunity.objects
            .filter(course=pctx.course)
            .order_by("identifier")))

    participations = list(Participation.objects
            .filter(
                course=pctx.course,
                status=participation_status.active,
                role=participation_role.student,)
            .order_by("user__last_name", "user__first_name")
            .prefetch_related("user"))

    grade_table = []
    for participation in participations:
        grade_row = []
        for opp in grading_opps:
            grade_changes = (GradeChange.objects
                    .filter(
                        participation=participation,
                        opportunity=opp)
                    .order_by("grade_time"))

            state_machine = GradeStateMachine()
            state_machine.consume(grade_changes)

            grade_row.append(
                    GradeInfo(
                        participation=participation,
                        opportunity=opp,
                        grade_state_machine=state_machine))

        grade_table.append(grade_row)

    return render_course_page(pctx, "course/gradebook.html", {
        "grade_table": zip(participations, grade_table),
        "grading_opportunities": grading_opps,
        "participations": participations,
        "grade_state_change_types": grade_state_change_types,
        })

# }}}

# vim: foldmethod=marker
