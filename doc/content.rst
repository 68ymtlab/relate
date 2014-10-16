Writing content for CourseFlow
==============================

.. _git-repo:

Git repository
--------------

In CourseFlow, one course corresponds to one Git repository.

Data for a course in CourseFlow is contained in a `git <http://git-scm.com/>`_
repository. CourseFlow understands the structure of a repository and makes use
of the version history present. For example, you could be previewing and
testing some newly developed course content, while the students continue to
work with a prior version until you make the new version explicitly available.

One revision ("commit") of the git repository is always viewed as the "current"
one. This is the one being shown to all visitors. In addition, each user (with
sufficient privileges) may be previewing a different version of their choosing.

YAML
----

Most of the files in the :ref:`git-repo` defining course content are written in
`YAML <http://yaml.org/>`_. YAML is a structured plain text format. If you know
what XML is: The conceptual idea is a little like XML, but YAML is much easier
to read and write by humans than XML.

Here's an example::

    title: "Homework 3"
    sticky_versioning: false
    description: |

        # Homework 3

        Welcome to our third homework set, where you will learn about principal component analysis,
        applications of linear least squares, and more.

    access_rules:
     - id: main
       start: lecture 12
       end: hw_due 3
       allowed_session_count: 1
       sticky: True
       permissions: [view, start_credit, view_past, see_correctness, change_answer, set_roll_over_expiration_mode]

     - id: grace
       start: hw_due 3
       end: hw_due 3 + 1 week
       allowed_session_count: 1
       credit_percent: 50
       sticky: True
       permissions: [view, start_credit, view_past, see_correctness, change_answer]

     - id: review
       start: hw_due 3 + 1 week
       permissions: [view, view_past, see_correctness, see_answer]

     - id: fallback
       permissions: []

     ...

Validation
----------

While YAML lets you define *arbitrary* structures, CourseFlow imposes a number of rules
on what your YAML documents should look like to be acceptable as course content.

These rules are automatically checked as part of setting a new revision of the
:ref:`git-repo` to be the active or previewed revision.

This helps avoid mistakes and ensures that the students always see a working
site.

CourseFlow validation is also available as a stand-alone script :cmd:`cf-validate`.
This runs independently of git and the web site on the content developer's
computer and provides validation feedback without having to commit and
upload the content to a CourseFlow site. This script can be installed by running::

    sudo pip install -r requirements.txt
    sudo python setup.py install

in the root directory of the CourseFlow distribution.

.. _markup:

CourseFlow markup
-----------------

All bulk text in CourseFlow is written in `Markdown
<http://daringfireball.net/projects/markdown/>`_, with a few extensions. The
linked page provides a (mostly) complete definition of the language.  A
10-minute `tutorial <http://markdowntutorial.com/>`_ is available to provide a
quick, approachable overview of Markdown.

In addition to standard Markdown, the following extensions are
supported:

Linking to flows
^^^^^^^^^^^^^^^^

The URL schema ``flow:flow-name`` provides a link to the start page of a
flow.

In Markdown, this might look like this::

    Please take [today's quiz](flow:quiz-lecture-17).

This resolves to a link to the flow contained in
:file:`flows/quiz-lecture-17.yml`.

URL schema for media (e.g. images)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The URL schema ``media:some/file/name.png``
will be resolved to the file `media/some/file/name.png` in the 
course's :ref:`git-repo`.

In Markdown, this might look like this::

    ![A bouncing ball](media:images/bouncing-ball.gif)

LaTeX-based mathematics
^^^^^^^^^^^^^^^^^^^^^^^

Use ``$...$`` to enclose inline math
and ``$$...$$`` to enclose display math. This feature is provided
by `MathJax <http://www.mathjax.org/>`_.

Symbols and Icons
^^^^^^^^^^^^^^^^^

CourseFlow includes `FontAwesome <http://fontawesome.io/>`_,
a comprehensive symbol set by Dave Gandy.
Symbols from `that set <http://fontawesome.io/icons/>`_ can be included as follows::

      <i class="fa fa-heart"></i>

In-line HTML
^^^^^^^^^^^^

In addition to Markdown, HTML is also allowed and puts the
full power of modern web technologies at the content author's disposal.
Markdown and HTML may also be mixed. For example, the following
creates a box with a recessed appearance around the content::

    <div class="well" markdown="1">
      Exam 2 takes place **next week**. Make sure to [prepare early](flow:exam2-prep).
    </div>

The attribute ``markdown="1"`` instructs CourseFlow to continue looking
for Markdown formatting inside the HTML element.

Video
^^^^^

CourseFlow includes `VideoJS <http://www.videojs.com/>`_
which lets you easily include HTML5 video in your course content.
The following snippet shows an interactive video viewer::

    <video id="myvideo" class="video-js vjs-default-skin"
       controls preload="auto" width="800" height="600"
       poster="/video/cs357-f14/encoded/myvideo.jpeg"
       data-setup='{"example_option":true}'>
      <source src="/video/cs357-f14/encoded/myvideo.webm" type='video/webm' />
      <source src="/video/cs357-f14/encoded/myvideo.mp4" type='video/mp4' />
      <p class="vjs-no-js">To view this video please enable JavaScript, and consider upgrading to a web browser that <a href="http://videojs.com/html5-video-support/" target="_blank">supports HTML5 video</a></p>
    </video>

Macros
^^^^^^

Repetitive text (such as the fairly long video inclusion snippet above)
can be abbreviated through the use of the `Jinja <http://jinja.pocoo.org/docs/dev/templates/>`_
templating language. To enable this support, make sure to use the line::

    [JINJA]

as the first line of your bulk text. From that point, you may use all features
of Jinja. For example, you could have a file :file:`macros.jinja` in the root
of your :ref:`git-repo` containing the following text::

    {% macro youtube(id) -%}
      <iframe width="420" height="315" src="//www.youtube.com/embed/{{id}}" frameborder="0" allowfullscreen>
      </iframe>
    {%- endmacro %}

This could then be used from wherever CourseFlow markup is allowed::

          [JINJA]

          Some text... More text...

          {% from "macros.jinja" import youtube %}

          {{ youtube("QH2-TGUlwu4") }}

          Some text... More text...

to embed a YouTube player. (YouTube is a registered trademark.)

Calendar and Events
-------------------

...
