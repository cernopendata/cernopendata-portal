==============
 Contributing
==============

Bug reports, feature requests and code contributions are encouraged
and welcome!

Bug reports and feature requests
--------------------------------

If you find a bug or have a feature request, please search for
`already reported problems
<https://github.com/cernopendata/cernopendata-portal/issues>`_ before
submitting a new issue.

If you would like to take more active part in the CERN Open Data
portal developments, you can `become part of the team
<https://github.com/orgs/cernopendata/teams>`_.

Code contributions
------------------

For information about how to work with the CERN Open Data portal, see our `developing guide <DEVELOPING.rst>`_.

The project follows the `GitHub flow
<https://docs.github.com/en/get-started/exploring-projects-on-github/contributing-to-a-project>`_
of forking repositories, creating branches, and submitting pull requests.
Check out our usual `contribution practices
<https://invenio.readthedocs.io/en/latest/community/contributing/contribution-guide.html>`_.

The key words "MUST", "SHOULD", "SHOULD NOT", and "MAY"
in this document are to be interpreted as described in `RFC 2119 <https://datatracker.ietf.org/doc/html/rfc2119>`_.

Before creating a pull request:

1. Changes MUST be tested and verified locally, and they MUST pass tests.
2. Commits MUST be logically separate for logically separate things, and commit messages MUST be clear and brief.
   This project follows `conventional commits specification <https://www.conventionalcommits.org/en/v1.0.0/>`_.
3. Any ``(closes #123)`` directives SHOULD be added to the commit message if the pull request closes an open issue.
4. Tests SHOULD be included and our
   `style guide <https://invenio.readthedocs.io/en/latest/community/contributing/style-guide.html#style-guide>`_
   MUST be followed.

Keep in mind that each pull request SHOULD be focused on one problem.

When creating the pull request, if the branch is not quite ready yet,
``WIP`` (=work in progress) SHOULD be indicated in the pull request title and it MUST be marked as a draft.

To be able to give every pull request a real review and to keep issues available for other contributors,
an outside contributor SHOULD NOT have more than one pull request open at a time.

AI Policy
---------

AI coding tools MAY be used. However, the contributions MUST meet the same standards as any other contribution. Keep in mind that:

- The use of AI assistants MUST be disclosed, e.g. ``Assisted-by: Claude Opus 5 (high effort)``.
- Quality and scope MUST be maintained, and the changes MUST be justified and necessary.
- The changes MUST be reviewed, tested, and verified yourself to ensure correctness, efficiency, security,
  and third-party rights before creating a pull request.

Treat the AI tools as assistants, and keep in mind that responsibility always stays with the person behind the change.

Maintainers may close issues and PRs that are not useful or productive, without explanation,
for example in the case of unverified AI-generated ("vibe-coded") contributions.
Keep in mind that submissions that show no sign of manual verification can be disruptive, counterproductive
and an unnecessary burden which slows down meaningful progress and therefore can be closed without review.
Repeated low-quality and unproductive submissions may lead to restrictions to contributing to the project because
it can be disruptive and disrespectful of the maintainers' time.
