# Contributor guide

## How to contribute

Government employees, public and members of the private sector are encouraged to contribute to the repository by **forking and submitting a pull request**.

(If you are new to GitHub, you might start with a [basic tutorial](https://help.github.com/articles/set-up-git) and  check out a more detailed guide to [pull requests](https://help.github.com/articles/using-pull-requests/).)

Pull requests will be evaluated by the repository guardians on a schedule and if deemed beneficial will be committed to the main branch.

All contributors retain the original copyright to their stuff, but by contributing to this project, you grant a world-wide, royalty-free, perpetual, irrevocable, non-exclusive, transferable license to all users **under the terms of the license under which this project is distributed.**

## Work item lifecycle

Our work is tracked in JIRA.

### Creating Work items

- Any team member can, and should, create Work items to prioritize and track the work.
- Check if the Work item already exists on the board.
- Work item Title: Noun + verb/action
- Add tags - Use the existing ones. Don't create tags. Talk with the team first!
- New Work items should remain in the backlog column and prioritized with the product owner

### Refining Work items

- Estimating/Reviewing work items async before refinement/sprint planning
- Backlog refinement/sprint planning meetings should happen before the end of the current sprint
- Work item should pass Definition of Ready (DoR) before it can be moved as a sprint candidate

## Managing Work items through stages

- Tracking work done on an work item using checkboxes
- When Work item is in development, draft PR should be created
- When development is complete and results satisfy Definition of Done, status of the PR should be changed to Open for review and Work item moved to appropriate column
- When PR is approved, work item can be moved to "PO review"

### Communication

- Update the Backlog before the Stand-up meeting
- Always mention the Work item in the conversation
- Communication takes place in the development channel in the Gov Team. Gov Teams is the main channel of communication between PO, Stakeholders and the team
- UEX/design and dev sync takes place in regular meetings [TBD] 2 devs at least for a design-dev sync or whole team?
- [TBD] designers write user stories and loop in developers for discussion during sync?

## Meetings

- Not invite everyone to all meetings. Be mindful of each meeting one of the team members should be present. (Required vs Optional)
- Feel free to leave a meeting if you feel you shouldn’t be there.
- [TBD] timed-box async backlog refinement?
- [TBD] Every meeting should have: Meeting Agenda? Meeting minutes? Action items?

## Development and Version Control

- Devs can appoint representatives for dev-design syncs
- Branch naming policy is as created by JIRA
- Make pull requests early and often to facilitate a transparent process.
- When a PR is ready, move the work item to dev review.
- Reviews can be done by the first person who gets to it. If the code needs explaining, request the author to walk you through it.
- Follow peer review best practices by suggesting opportunities to improve code during peer review, merging as soon as the code is better than the code in the target branch and release ready.
- Treat any opportunity for improvement feedback identified during peer review but not implemented in the PR where it was raised as technical debt worthy of a new Work item referencing the PR where the comments first came up.
- When necessary, use git rebase to sync a feature branch with main. This keeps a tidier history in git, however, can be destructive, so do so cautiously.

**Guardrails**

- The following guardrails are in place to ensure we keep a clean working tree, while avoiding merging breaking changes into our main branch.
- The default branch for this repo is main.
- All commits must be made to a non-protected branch and submitted via a pull request before they can be merged into main. (There can be no direct commits made to main.)
- Branches are automatically deleted on Github when a PR is merged. Each teammate should set git config fetch.prune true to mirror this behaviour to their local workstation.
- Squash merge has been disabled to increase the efficiency of git bisect.

## Signing commits

Signed commits are a requirement to merge code into this project to give the team confidence of the origin of a change that has been made. This is enforced so that all commits in a pull request must have verified signatures before they are merged into main.

[About commit signature verification](https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification)
[Signing commits](https://docs.github.com/en/authentication/managing-commit-signature-verification/signing-commits)

## Commit Message Guidelines

Similar to [Angular's guidelines](https://github.com/angular/angular/blob/22b96b9/CONTRIBUTING.md#-commit-message-guidelines), we follow the [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/) format for our commit messages. This leads to more readable messages that are easy to follow when looking through the project history. We use the git commit messages to generate the change log upon releasing.

The commit message header must be formatted as follows:

`<type>[(optional scope)]: <description>`

### Type

Must be one of the following:

- **ci**: Changes to our CI configuration files and scripts
- **docs**: Documentation-only changes
- **feat**: A new feature, either user-facing or in the backend
- **fix**: A bug fix
- **perf**: A code change that improves performance
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **style**: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)
- **test**: Adding missing tests or correcting existing tests
- **chore**: Any other type of change

### Breaking changes

If the change is a breaking change, add a `!` after the type, e.g. `feat!`. A breaking change is any change that would require manual intervention from a team member or a user to ensure business continuity.

### Scope

To make it easier for the reader to identify the scope of the change, you _may_ indicate a scope in your commit message.
If a change affects multiple scopes, do not provide a scope in your commit message.
The following scopes may be used:

- **front-end**: for changes that affect only the front-end code
- **backend**: for changes that affect the backend code
- **db**: for changes that affect the database code
- **devops**: for changes that affect the deployment configurations, such as the terraform config
- **deps**: for changes that affect the application's dependencies