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

import re
import datetime
import six

from course.content import get_yaml_from_repo, get_repo_blob


# {{{ validation tools

class ValidationError(RuntimeError):
    pass


ID_RE = re.compile(r"^[\w]+$")


def validate_identifier(location, s):
    if not ID_RE.match(s):
        raise ValidationError("%s: invalid identifier '%s'"
                % (location, s))


def validate_role(location, role):
    from course.models import participation_role

    if role not in [
            participation_role.instructor,
            participation_role.teaching_assistant,
            participation_role.student,
            participation_role.unenrolled,
            ]:
        raise ValidationError("%s: invalid role '%s'"
                % (location, role))


def validate_struct(location, obj, required_attrs, allowed_attrs):
    """
    :arg required_attrs: an attribute validation list (see below)
    :arg allowed_attrs: an attribute validation list (see below)

    An attribute validation list is a list of elements, where each element is
    either a string (the name of the attribute), in which case the type of each
    attribute is not checked, or a tuple *(name, type)*, where type is valid
    as a second argument to :func:`isinstance`.
    """

    present_attrs = set(name for name in dir(obj) if not name.startswith("_"))

    for required, attr_list in [
            (True, required_attrs),
            (False, allowed_attrs),
            ]:
        for attr_rec in attr_list:
            if isinstance(attr_rec, tuple):
                attr, allowed_types = attr_rec
            else:
                attr = attr_rec
                allowed_types = None

            if attr not in present_attrs:
                if required:
                    raise ValidationError("%s: attribute '%s' missing"
                            % (location, attr))
            else:
                present_attrs.remove(attr)
                val = getattr(obj, attr)

                if not isinstance(val, allowed_types):
                    raise ValidationError("%s: attribute '%s' has "
                            "wrong type: got '%s', expected '%s'"
                            % (location, attr, type(val).__name__,
                            allowed_types))

    if present_attrs:
        raise ValidationError("%s: extraneous attribute(s) '%s'"
                % (location, ",".join(present_attrs)))


datespec_types = (datetime.date, six.string_types)

# }}}


class ValidationContext(object):
    def __init__(self, repo, commit_sha):
        self.repo = repo
        self.commit_sha = commit_sha


# {{{ course page validation

def validate_chunk_rule(ctx, chunk_rule):
    validate_struct(
            "chunk_rule",
            chunk_rule,
            required_attrs=[
                ("weight", int),
                ],
            allowed_attrs=[
                ("start", (str, datetime.date)),
                ("end", (str, datetime.date)),
                ("role", str),
                ("shown", bool),
            ])


def validate_chunk(ctx, chunk):
    validate_struct(
            "chunk",
            chunk,
            required_attrs=[
                ("title", str),
                ("id", str),
                ("rules", list),
                ("content", str),
                ],
            allowed_attrs=[]
            )

    for rule in chunk.rules:
        validate_chunk_rule(ctx, rule)


def validate_course_desc_struct(ctx, course_desc):
    validate_struct(
            "course_desc",
            course_desc,
            required_attrs=[
                ("name", str),
                ("number", str),
                ("run", str),
                ("description", str),
                ("course_start", datetime.date),
                ("course_end", datetime.date),
                ("chunks", list),
                ],
            allowed_attrs=[]
            )

    for chunk in course_desc.chunks:
        validate_chunk(ctx, chunk)

# }}}


# {{{ flow validation

def validate_flow_page(ctx, location, page_desc):
    validate_identifier(location, page_desc.id)

    from course.content import instantiate_flow_page
    try:
        instantiate_flow_page(location, ctx.repo, page_desc, ctx.commit_sha)
    except ValidationError as e:
        raise ValidationError("%s: %s" % (location, str(e)))
    except Exception as e:
        raise ValidationError(
                "%s: could not instantiate flow page: %s: %s"
                % (location, type(e).__name__, str(e)))


def validate_flow_group(ctx, location, grp):
    validate_struct(
            location,
            grp,
            required_attrs=[
                ("id", str),
                ("pages", list),
                ],
            allowed_attrs=[]
            )

    for i, page_desc in enumerate(grp.pages):
        validate_flow_page(
                ctx,
                "%s, page %d ('%s')" % (location, i+1, page_desc.id),
                page_desc)

    validate_identifier(location, grp.id)

    # {{{ check page id uniqueness

    page_ids = set()

    for page_desc in grp.pages:
        if page_desc.id in page_ids:
            raise ValidationError("%s: page id '%s' not unique"
                    % (location, page_desc.id))

        page_ids.add(page_desc.id)

    # }}}


def validate_flow_permission(ctx, location, permission):
    from course.models import FLOW_PERMISSION_CHOICES
    if permission not in dict(FLOW_PERMISSION_CHOICES):
        raise ValidationError("%s: invalid flow permission"
                % location)


def validate_flow_access_rule(ctx, location, rule):
    validate_struct(
            location,
            rule,
            required_attrs=[
                ("permissions", list),
                ],
            allowed_attrs=[
                ("roles", list),
                ("start", (datetime.date, str)),
                ("end", (datetime.date, str)),
                ("credit_percent", (int, float)),
                ("time_limit", str),
                ("allowed_visit_count", int),
                ]
            )

    for i, perm in enumerate(rule.permissions):
        validate_flow_permission(
                ctx,
                "%s, permission %d" % (location, i+1),
                perm)

    if hasattr(rule, "roles"):
        for i, role in enumerate(rule.roles):
            validate_role(
                    "%s, role %d" % (location, i+1),
                    role)

    # TODO: validate time limit


def validate_flow_desc(ctx, location, flow_desc):
    validate_struct(
            location,
            flow_desc,
            required_attrs=[
                ("title", str),
                ("description", str),
                ("groups", list),
                ("completion_text", str),
                ],
            allowed_attrs=[
                ("access_rules", list),
                ]
            )

    if hasattr(flow_desc, "access_rules"):
        for i, rule in enumerate(flow_desc.access_rules):
            validate_flow_access_rule(ctx,
                    "%s, access rule %d" % (location, i+1),
                    rule)

        last_rule = flow_desc.access_rules[-1]
        if (
                hasattr(last_rule, "roles")
                or hasattr(last_rule, "start")
                or hasattr(last_rule, "end")
                ):
            raise ValidationError("%s: last access rule must set default access "
                    "(i.e. have no attributes other than 'permissions')"
                    % location)

    # {{{ check for non-emptiness

    flow_has_page = False
    for i, grp in enumerate(flow_desc.groups):
        group_has_page = False

        for page in grp.pages:
            group_has_page = flow_has_page = True
            break

        if not group_has_page:
            raise ValidationError("%s, group %d ('%d'): no pages found"
                    % (location, i+1, grp.id))

    if not flow_has_page:
        raise ValidationError("%s: no pages found"
                % location)

    # }}}

    # {{{ check group id uniqueness

    group_ids = set()

    for grp in flow_desc.groups:
        if grp.id in group_ids:
            raise ValidationError("%s: group id '%s' not unique"
                    % (location, grp.id))

        group_ids.add(grp.id)

    # }}}

    for i, grp in enumerate(flow_desc.groups):
        validate_flow_group(ctx, "%s, group %d ('%s')"
                % (location, i+1, grp.id),
                grp)

# }}}


def validate_course_content(repo, validate_sha):
    course_desc = get_yaml_from_repo(repo, "course.yml",
            commit_sha=validate_sha)

    ctx = ValidationContext(repo=repo, commit_sha=validate_sha)
    validate_course_desc_struct(ctx, course_desc)

    flows_tree = get_repo_blob(repo, "flows", validate_sha)

    for entry in flows_tree.items():
        location = "flows/%s" % entry.path
        flow_desc = get_yaml_from_repo(repo, location,
                commit_sha=validate_sha)

        validate_flow_desc(ctx, location, flow_desc)

# }}}

# vim: foldmethod=marker
