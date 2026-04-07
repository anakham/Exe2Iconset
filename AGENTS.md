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

## Workflow Contract

This defines how AI and human collaborate. Roles can reverse, and iterations are allowed.

### Core Principle
- Task-giver approves each step before execution
- Task-executor shows results after each step

### Standard Flow (AI executes, human approves)

1. **Task Assignment** - Human describes what needs to be done
2. **Research & Plan** - AI analyzes, reads files, creates plan
3. **Plan Approval** - Human reviews and confirms plan
4. **Implementation** - AI makes changes locally
5. **Run Tests** - Command: `PYTHONPATH=. pytest tests/`
6. **Show Results** - Command: `git diff` or `git diff <file>`
7. **Approval** - Human says "ready to commit"
8. **Commit** - Command: `git add <files> && git commit -m "message"`
9. **Approval** - Human says "ready to push"
10. **Push** - Command: `git push`
11. **PR Interaction** - Reply/comments with approval

### Reversed Flow (Human executes, AI reviews)

1. **AI Proposes** - AI shows plan or code changes
2. **Human Executes** - Human commits/pushes
3. **AI Reviews** - AI checks, suggests fixes

### Loops

- **Pre-PR iterations**: Fix until all tests pass, human approves
- **PR review cycles**: Address comments → reply → iterate until resolved

### Responsibilities

| Action | Who Does It | Who Approves |
|--------|-------------|--------------|
| Task description | Either | - |
| Research/analysis | AI | - |
| Code changes | Either | Task-giver |
| Tests | AI | - |
| Commit | Either | Task-giver |
| Push | Either | Task-giver |
| PR replies | Either | Task-giver |
| PR merge | Either | Task-giver |

---

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
