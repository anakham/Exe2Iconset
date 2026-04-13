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
│   └── core/                 # Core modules
│       ├── __init__.py
│       ├── convert.py        # Icon conversion/resizing
│       ├── extract.py        # PE file icon extraction
│       └── icns.py           # ICNS file creation
├── tests/                    # Test suite (pytest)
│   ├── conftest.py          # Shared pytest fixtures
│   ├── test_convert.py
│   ├── test_extract.py
│   └── test_icns.py
├── sessions/                 # Session logs for context
└── README.md
```

---

## Workflow

This defines how AI agent and human collaborate. Roles can reverse, and iterations are allowed.

### Core Principles

This workflow does not include planning process, in which milestones and it's main set of issues are generated. It considers developement stages splited in following main categories:

* Issue triage
* Code development (creation of commits)
* Code review (creation and closing of pull requests)
* Issue closing

Detailed description of these stages presented in next paragraphs.  

### Issue Triage

1. **Task Assignment**. Human selects issue to solve from projects issue. AI agent helps with projects unresolved issue representation if needed. After Issue is selected for developement. If milestone and project issue links not set, AI agents sets them eigher. Commands to be used for:
    - issue list: <command_placeholder>
    - project and milestone setting: <command_placeholder>
2. **Task Planing**. If scope of issue is large then it could be divided into subissues. After creating subissues return to 1. Commands for:
    - issue creation: <command_placeholder>
    - setting sub-issue relationship: <command_placeholder>
3. **Start implementation**. AI agent sets issue assignee (human or himself). Proceed to **Code Development**. Command for:
    - assignee setting: <command_placeholder>

### Code Development

4. **Implementation**. Assignee makes changes or experiments locally
5. **Create Branch**. Create developement branch if code changes are required else proceed to **Issue Closing** stage. Command for:
    - branch creation: <command_placeholder>, format of branch name: `[feature|bug]/issue-<issue_number>-<concise-branch-name>`
6. **Run Tests**. Command for:
    - running tests: `PYTHONPATH=. pytest tests/`
7. **Precommit Review**. Reviewers examines changes and make remarks. Them can also propose changes to code and documents in working copy. Asignee takes that remarks into consideration and makes or accepts necessary changes. If asked assignee makes intermidiate local commits (with amend if it is not first commit and fix were minor) for better track remark fixes and do them iteratively by small steps and not all at once. Commands for:
    - viewing what's changed: `git diff` or `git diff <file>`
    - amend commit: <command_placeholder>
8. **Commit approval**. If reviewer confirms commit is ready, assignee do final commit with summary in commit message. Command for:
    - final commit: `git add <files> && git commit [--amend] -m "message"`
9. **Commit message review**. Before making push to git, commit message should be reviewed by reviewer. If were are remarks for commit message, they should be fixed by assignee and amended. Command for:
    - commit message amend: <command_placeholder>
10. **Push Approval**. All git push commands should be explicitly approved by human, AI agent can not do it automatically. After push, proceed to **Code Review** section. Command for:
    - push: `git push`

### Code Review

11. **PR Creation**. After first push on current issue branch, pull request should be created. It should be linked to project, it's milestone. Assignee should be set to account affiliated with AI agent or human. Reviewer also should be set. It is also to point out which issue cuurent pr is closing by adding finish line "Closes #<issue number>" in pr body description. Commands for:
    - pull request creation: <command_placeholder>
    - link pull request to project and milestone: <command_placeholder>
    - set pull request assignee and reviewer: <command_placeholder>
12. **PR Remarks**. Reviewer makes remarks and places them at the corespondent lines of code. If reviewer is AI agent then command for:
    - place first level comments in PR:
13. **PR Create Issue**.  
14. **PR Resolve Remarks**. Assignee reads remarks and for all of unresolved eigher prepare neccesary code changes (going back to **Code Development** stage) or if solving problems pointed by reviewer is hard and requires massive changes of code then new issue should be created for that by assignee. Weather it is the case, human should decide and confirm issue creation. In case issue is created, it's link should be place in the reply to the source replye comment. In case of code changes small reply to reviewer comment with fix summary should be placed. Commands for:
    - get list of all unresolved remarks: <command_placeholder>
    - new issue creation: <command_placeholder>
    - commentary as reply to pr comment: <command_placeholder>
15. **PR Confirm Remarks Fix**. Reviewer checks solutions for remarks, and either mark them as resolved, or reply with reason, why it consider it unresolved. Also reviewer may add some new remarks. After that **Code Review** stage repeats from begining until all remarks are resolved. Commands for:
    - setting resolved commentary mark (if reviewer is AI agent): <command_placeholder>
    - adding comment as reply to comment: <command_placeholder>
16. **PR Closure**. PR can be closed only if it has no unresolved reviewer remarks and human directly approved it is done. Comment describing whole developement process of this pull request may be added. Approved pull request should be merged to main branch with squach commits strategy. Commands for:
    - adding comment to pr not assigned to code: <command_placeholder>
    - merge pull request with squash commit strategy: <command_placeholder>

### Issue Closing

17. **Issue Close**. If issue is not closed by PR closing, close it. Command for:
    - set close issue state: <command_placeholder>
18. **Save AI development logs**. This step is optional. Human saves session logs from time to time as markdown files to `sessions\issue<#issue>` folder. Files may overlap (every next file may contain at the begining portion of the end of previous file). Compaction may take place. First lines of first files may relate to other issue. AI agent should create one file in format `YEAR-MONTH-DAY_session_<file_index>_issue_<issue_number>_<short_session_description>.md`. This file should be placed to project as gist and link to that gist should be attached to issue comment. Commands for:
    - gist placement: <command_placeholder>
    - adding gist link to issue coment: <command_placeholder>

That finalize work on issue.

## GitHub/PR Procedures

### Finding PR Review Comments

To find review threads in a PR with all details including line numbers:

```bash
gh api graphql -f query='{repository(owner: "OWNER", name: "REPO") { 
  pullRequest(number: N) { 
    reviewThreads(first: 20) { 
      nodes { 
        id 
        isResolved
        comments(first: 1) { 
          nodes { id body path line } 
        } 
      } 
    } 
  } 
 } }'
```

Key fields:
- `path`: File being commented on
- `line`: Line number in the diff (can be null)
- `isResolved`: Boolean - whether the thread is resolved
- `id`: Comment ID (use for replying)
- `thread_id`: The thread ID (use for `gh pr-review comments reply`)

Alternative - get simple list (REST API - returns line and side):
```bash
gh api repos/OWNER/REPO/pulls/N/comments --jq '.[] | {id: .id, path: .path, body: .body, line: .line, side: .side}'
```

Key fields:
- `path`: File being commented on
- `line`: Line number in the diff (can be null)
- `side`: RIGHT (shows diff context) or LEFT (shows deleted lines)
- `id`: Comment ID (use for replying)

### Replying to PR Review Comments

Use the thread ID from above:

```bash
gh pr-review comments reply N --repo OWNER/REPO --thread-id THREAD_ID --body "Your reply"
```

### Updating PR Description

```bash
gh api repos/OWNER/REPO/pulls/N -X PATCH -F body="New description text"
```

### Merging PR

```bash
gh pr merge N --squash --delete-branch
```

---

## Git Commands Reference

### When to Use --amend

Use `git commit --amend` ONLY when:
1. You just created the commit in this session (not yet pushed)
2. The commit was created by you (the AI) in this conversation
3. You need to add a small fix/revision to the most recent commit

**NEVER amend commits that:**
- Have already been pushed to remote
- Were created by someone else
- Are part of a published history

**Commands:**
```bash
# Amend the last commit
git commit --amend

# Amend with new message
git commit --amend -m "New message"

# Amend to add files
git add <files> && git commit --amend --no-edit
```

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
