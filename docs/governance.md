# Repository governance

## Protected branches

`main` is protected. Changes must use a pull request and satisfy:

- the branch is current with `main`;
- `action-smoke` passes;
- tests pass on Python 3.10, 3.11, and 3.12;
- conversations are resolved;
- commit history remains linear;
- force-pushes and branch deletion are disabled.

The rules apply to administrators. The required approval count is currently zero because DataPR has one maintainer; requiring an independent approval would prevent routine maintenance. Once a second active maintainer exists, the target state is one approval plus last-pusher separation.

The intentionally failing [dogfood PR #1](https://github.com/yvetteYSY/datapr/pull/1) is not a merge candidate. It exists to demonstrate policy enforcement and should remain unmerged.

## Change discipline

- Public contract changes require golden JSON tests and result-format documentation.
- Finding behavior changes require representative fixtures.
- Security-sensitive changes use private vulnerability reporting when appropriate.
- Architecture decisions that constrain later implementations should receive an ADR.
