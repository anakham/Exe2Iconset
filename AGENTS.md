# Exe2Iconset Agent Guidelines

This file provides instructions for AI coding assistants working on the Exe2Iconset project.

## Project Overview

Exe2Iconset is a cross-platform tool to extract icons from Windows EXE/DLL files and create macOS ICNS files. It includes a GUI application and CLI tool.

## Project Structure

```
Exe2Iconset/
├── exe2iconset/              # Main package
│   ├── __init__.py           # Package exports, version
│   ├── __main__.py           # Entry point for python -m exe2iconset
│   ├── cli.py                # Command-line interface
│   ├── gui.py                # Tkinter GUI application
│   ├── gui_dialogs.py        # Custom dialogs (FilePicker)
│   └── core/                 # Core modules
│       ├── __init__.py
│       ├── convert.py        # Icon conversion/resizing
│       ├── extract.py        # PE file icon extraction, unified extract_images()
│       ├── images.py         # Image file/directory extraction
│       └── icns.py           # ICNS file creation
├── scripts/                   # Build and development scripts
│   ├── build_app.py          # Cross-platform build script
│   └── vmware_dev_helpers/   # VM automation scripts
├── assets/                    # Icons and build assets
│   ├── icon/                 # App icons (.icns, .ico)
│   └── dmg_content/          # DMG files and assets
│       ├── generate_dmg_background.py  # DMG background generator
│       ├── Exit Quarantine.txt
│       └── Terminal.app -> /System/Applications/Utilities/Terminal.app
├── tests/                    # Test suite (pytest)
│   ├── conftest.py          # Shared pytest fixtures
│   ├── test_convert.py
│   ├── test_extract.py
│   └── test_icns.py
├── .github/workflows/        # CI/CD workflows
│   ├── build-release.yml    # Build and release workflow
│   ├── publish.yml          # PyPI publish workflow
│   └── test.yml             # Test workflow
├── exe2iconset.spec         # PyInstaller spec file
├── BUILD.md                 # Build instructions
├── sessions/                 # Session logs for context
└── README.md
```

---

## Workflow

This defines how AI agent and human collaborate. Roles can reverse, and iterations are allowed.

### Core Principles

This workflow does not include the planning process, in which milestones and the main set of issues are generated. It considers development stages split in the following main categories:

* Issue triage
* Code development (creation of commits)
* Code review (creation and closing of pull requests)
* Issue closing

Detailed description of these stages is presented in the next paragraphs.  

### Issue Triage

1. **Task Assignment**. Human selects issue to solve from project's issue. AI agent helps with project's unresolved issue representation if needed. After issue is selected for development. If milestone and project issue links not set, AI agent sets them either. Commands to be used for:
    - issue list: `gh issue list --json number,state,title | jq -r '.[] | "\(.number)\t\(.state)\t\(.title)"'`
    - issue details: `gh issue view N --json number,title,body,state,milestone,assignees,author,projectItems --jq '"number: \(.number)\ntitle: \(.title)\nstate: \(.state)\nmilestone: \(.milestone.title)\nassignee: \(.assignees[].login // "unassigned")\nauthor: \(.author.login)\nproject: \(.projectItems[].title // "none")\n\n\(.body)"'`
    - projects list: `gh project list --owner USERNAME` where USERNAME in the scope of this project is anakham.
    - project setting: `gh api graphql -f query='mutation { addProjectV2ItemById(input: { projectId: "PROJECT_ID", contentId: "ISSUE_NODE_ID" }) { clientMutationId } }'` where PROJECT_ID from `gh project list --owner USERNAME` and ISSUE_NODE_ID from `gh issue view N --json id`
    - milestone setting: `gh issue edit N --milestone "MilestoneName"`
2. **Task Planning**. If scope of issue is large then it could be divided into subissues. After creating subissues return to 1. Commands for:
    - issue creation: `gh issue create --title "Title" --body "Description" [--milestone "MilestoneName"] [--label "label"] [--assignee @me]` (Note: project setting must be done separately after creation via project/milestone setting command)
    - setting sub-issue relationship: `gh api graphql -f query='mutation { addSubIssue(input: { issueId: "PARENT_ISSUE_ID", subIssueId: "SUB_ISSUE_ID" }) { subIssue { id number title } } }'` where PARENT_ISSUE_ID from `gh issue view N --json id` and SUB_ISSUE_ID from `gh issue view M --json id`
3. **Start implementation**. AI agent sets issue assignee (human or himself). Proceed to **Code Development**. Command for:
    - assignee setting: `gh issue edit N --add-assignee @me` or `gh issue edit N --add-assignee USERNAME`

### Code Development

4. **Implementation**. Assignee makes changes or experiments locally
5. **Create Branch**. Create development branch if code changes are required else proceed to **Issue Closing** stage. Command for:
    - branch creation: `git checkout -b [feature|bug]/issue-<issue_number>-<concise-branch-name>`, format of branch name: `[feature|bug]/issue-<issue_number>-<concise-branch-name>`
6. **Run Tests**. Command for:
    - running tests: `PYTHONPATH=. pytest tests/`
7. **Precommit Review**. Reviewers examines changes and make remarks. Them can also propose changes to code and documents in working copy. Assignee takes that remarks into consideration and makes or accepts necessary changes. Commands for:
    - viewing what's changed: `git diff` or `git diff <file>`
8. **Commit approval**. AI agent must ALWAYS ask for explicit human approval before making any commit (including intermediate/fix commits). Use the `question` tool to ask. Only after human explicitly approves, proceed with the commit. Use `git commit --amend` ONLY when: (1) created by you this session, (2) not yet pushed, (3) small fix needed. NEVER amend commits that were pushed, created by others, or are published. For a small fix, ask human: amend, new commit, or wait. Commands for:
    - final commit: `git add <files> && git commit -m "message"`
    - amend (add files): `git add <files> && git commit --amend --no-edit`
    - amend (change message): `git commit --amend -m "New message"`
    - amend (bare): `git commit --amend`
9. **Commit message review**. Commit message should be reviewed before push. If there are remarks, amend the message (see step 8 for amend commands).
10. **Push Approval**. All git push commands require explicit human approval. AI agent must use the `question` tool to ask for approval. Only proceed with push when human responds with "push approved". After push, proceed to **Code Review** section. Commands for:
    - first push (when branch doesn't exist on remote): `git push -u origin branch-name`
    - subsequent push: `git push`

### Code Review

11. **PR Creation**. After first push on current issue branch, pull request should be created. It should be linked to project, its milestone. Assignee should be set to account affiliated with AI agent or human. Reviewer also should be set. It is also to point out which issue current PR is closing by adding closing line "Closes #<issue number>" in PR body description. Commands for:
    - pull request creation: `gh pr create --title "Title" --body "Description" --base main --head branch-name` (Note: add "Closes #N" in body to close issue)
    - link pull request to project: `gh api graphql -f query='mutation { addProjectV2ItemById(input: { projectId: "PROJECT_ID", contentId: "PR_NODE_ID" }) { clientMutationId } }'` where PROJECT_ID from `gh project list --owner USERNAME` and PR_NODE_ID from `gh pr view N --json id`
    - set pull request milestone: `gh api graphql -f query='mutation { updatePullRequest(input: { pullRequestId: "PR_NODE_ID", milestoneId: "MILESTONE_NODE_ID" }) { clientMutationId } }'` where MILESTONE_NODE_ID from `gh api repos/OWNER/REPO/milestones/N --jq '.node_id'`
    - set pull request assignee: `gh api graphql -f query='mutation { addAssigneesToAssignable(input: { assignableId: "PR_NODE_ID", assigneeIds: ["USER_ID"] }) { clientMutationId } }'` where USER_ID from `gh api graphql -f query='{user(login: "USERNAME") { id } }'`
    - set pull request reviewer: `gh api graphql -f query='mutation { requestReviews(input: { pullRequestId: "PR_NODE_ID", userIds: ["USER_ID"] }) { clientMutationId } }'` where USER_ID from `gh api graphql -f query='{user(login: "USERNAME") { id } }'` (Note: PR creator cannot be a reviewer - use a different account)
    - update PR description: `gh api repos/OWNER/REPO/pulls/N -X PATCH -F body="New description"`
12. **PR Remarks**. Reviewer makes remarks and places them at the correspondent lines of code. If reviewer is AI agent then commands for:
    - get PR node ID: `gh api graphql -f query='{repository(owner:"OWNER", name:"REPO") { pullRequest(number: N) { id } }}'`
    - add line comment (GraphQL): `gh api graphql -f query='mutation { addPullRequestReviewThread(input: { pullRequestId: "PR_NODE_ID", line: LINE_NUMBER, side: RIGHT, body: "Comment text", path: "path/to/file.py" }) { thread { id } } }'`
    - add line comment (REST): `gh api repos/OWNER/REPO/pulls/N/comments -X POST -F body="Comment" -F commit_id=COMMIT_SHA -F path=FILENAME -F line=LINE -F side=RIGHT`
13. **PR Resolve Remarks**. Assignee reads remarks and for all of unresolved either prepares necessary code changes (going back to **Code Development** stage) or if solving problems pointed by reviewer is hard and requires massive changes of code then new issue should be created for that by assignee. Whether it is the case, human should decide and confirm issue creation. In case issue is created, its link should be placed in the reply to the source reply comment. In case of code changes, small reply to reviewer comment with fix summary should be placed. Commands for:
    - list all review comments (REST): `gh api repos/OWNER/REPO/pulls/N/comments --jq '.[] | {id: .id, path: .path, body: .body, line: .line, side: .side}'`
    - list unresolved review threads (GraphQL): `gh api graphql -f query='{repository(owner: "OWNER", name: "REPO") { pullRequest(number: N) { reviewThreads(first: 100) { nodes { id isResolved comments(first: 1) { nodes { path line body } } } } } } }' | jq -r '.data.repository.pullRequest.reviewThreads.nodes[] | if .isResolved == false then "[\(.id)] \(.comments.nodes[0].path // "general"):\(.comments.nodes[0].line // "?") - \(.comments.nodes[0].body[:50])..." else empty end'`
    - reply to comment thread: `gh pr-review comments reply N --repo OWNER/REPO --thread-id THREAD_ID --body "Your reply"`
    - create new issue: `gh issue create --title "Title" --body "Description" [--milestone "MilestoneName"] [--label "label"] [--assignee @me]` (Note: If issue created, link it in reply using thread ID)
    - find comment IDs (for deletion): `gh api graphql -f query='{repository(owner:"OWNER", name:"REPO") { pullRequest(number: N) { reviewThreads(first: 100) { nodes { id line comments(first:5) { nodes { id body } } } } } } }'`
    - delete line comment: `gh api graphql -f query='mutation { deletePullRequestReviewComment(input: {id: "PRRC_ID"}) { clientMutationId } }'`
    - delete PR/issue comment: `gh api graphql -f query='mutation { deleteIssueComment(input: {id: "IC_ID"}) { clientMutationId } }'`
14. **PR Confirm Remarks Fix**. Reviewer checks solutions for remarks, and either marks them as resolved, or replies with reason why they consider it unresolved. Also reviewer may add some new remarks. After that **Code Review** stage repeats from beginning until all remarks are resolved. Commands for:
    - resolve thread: `gh api graphql -f query='mutation { resolveReviewThread(input: { threadId: "THREAD_ID" }) { clientMutationId } }'`
    - unresolve thread: `gh api graphql -f query='mutation { unresolveReviewThread(input: { threadId: "THREAD_ID" }) { clientMutationId } }'`
    - reply to thread: `gh pr-review comments reply N --repo OWNER/REPO --thread-id THREAD_ID --body "Your reply"`
15. **PR Closure**. PR can be closed only if it has no unresolved reviewer remarks and human directly approved it is done. Comment describing whole development process of this pull request may be added. Approved pull request should be merged to main branch with squash commits strategy. Commands for:
    - approve PR: `gh pr review N --approve`
    - request changes: `gh pr review N --request-changes --body "Description of changes needed"`
    - comment only (no approval/status): `gh pr review N --body "Comment text"`
    - check for unresolved remarks: `gh api graphql -f query='{repository(owner: "OWNER", name: "REPO") { pullRequest(number: N) { reviewThreads(first: 100) { nodes { id isResolved comments(first: 1) { nodes { path line body } } } } } } }' | jq -r '.data.repository.pullRequest.reviewThreads.nodes[] | if .isResolved == false then "[\(.id)] \(.comments.nodes[0].path // "general"):\(.comments.nodes[0].line // "?") - \(.comments.nodes[0].body[:50])..." else empty end'` (should return empty; increase `first:` value or add pagination `after:` cursor if PR has more than 100 threads)
    - add general comment to PR: `gh pr comment N --body "Comment text"`
    - merge PR with squash: `gh pr merge N --squash --delete-branch`

Note: A user cannot approve their own PR. The PR creator must use a different account to approve.

### Issue Closing

16. **Issue Close**. If issue is not closed by PR closing, close it. Command for:
    - set close issue state: `gh issue close N`
17. **Save AI development logs**. This step is optional. The session logger plugin saves logs to `sessions/` with a `current_session.md` symlink pointing to the active file. Use one session per issue. When saving, resolve the symlink and upload the log as a gist, then link it in an issue comment. Commands for:
    - get current session file: `readlink sessions/current_session.md`
    - create gist from session file: `gh gist create --filename "FILENAME.md" --desc "Session logs for issue #N" sessions/CURRENT_SESSION_FILENAME`
    - add gist link to issue comment: `gh issue comment N --body "Session logs: https://gist.github.com/GIST_ID"`

That finalize work on issue.

---

## Code Standards

- Follow existing code patterns in the codebase
- Use type hints where beneficial
- Add docstrings to new functions
- No TODO comments without issue reference

## Testing

**Always run tests before committing:**

```bash
PYTHONPATH=. pytest tests/
```

**All tests must pass** before any commit.

## Documentation

- Keep README.md updated for any CLI/API changes
- Document new features with examples
- Update this AGENTS.md if workflow changes

## Session Files

Important discussions are saved in `sessions/` directory. Check there for context on previous decisions.
