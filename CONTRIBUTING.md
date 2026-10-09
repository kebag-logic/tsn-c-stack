# Contributing

Start from a tracked issue with a clear scope and acceptance criteria.
Keep protocol behavior changes separate from moves and licence changes.
Follow the [coding standard](docs/CODING_STANDARD.md) and [verification guide](docs/VERIFICATION.md).

Submit a pull request against the default branch. Explain the defect or need,
the resulting behavior, and the validation evidence.
Two independent positive reviews are required, including one outside the
implementation lane. The author cannot supply either approval.
The repository stays private until the required licence and documentation
reviews have merged. Publication is a separate owner action.

Use one-line commit subjects. Use no body, trailers or attribution footer.
Use neutral role labels in public documentation.
Keep host locations, account details, private equipment identifiers and assistant
product names out of source, documents and commit history.
Preserve existing copyright lines. Add the MIT SPDX identifier to new source.
See the [licence](LICENSE), [privacy gate](scripts/check_privacy.py) and
[security policy](SECURITY.md).

A protocol change updates its [requirement](docs/REQUIREMENTS.md), tests and
[traceability](docs/TRACEABILITY.md). A regression needs a failing assertion and
a runnable planted defect. Do not lower the [coverage ratchet](tests/coverage.ratchet)
to accommodate an untested path.
