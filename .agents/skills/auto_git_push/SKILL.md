---
name: auto-git-push-on-working-code
description: >-
  Mandatory workflow to automatically commit and push code changes to the git remote
  repository as soon as code is verified working and all tests pass. Enforces pre-push
  verification, clean conventional commits, and verification of remote synchronization.
always_on: true
---

# Auto Git Push on Working Code Workflow

Whenever modifying, implementing, refactoring, or updating code, configurations, or documentation:

## Core Rule: "Working Code Must Be Pushed"

As soon as a task, feature, bug fix, or modification is verified working (tests pass, build succeeds, no regressions), **immediately stage, commit, and push the changes to the git remote repository (`origin`)**. Do not wait for the user to explicitly ask to push.

---

## Standard 4-Step Push Workflow

### Step 1: Pre-Push Working Code Verification
Before any commit or push, verify that the code actually works:
1. Run the test suite or verification command relevant to the changes:
   - Python: `pytest <affected_tests>` or `pytest tests/`
   - JavaScript/TypeScript: `npm test` or `npm run build`
   - Backend/API: Health check probe or endpoint test
2. **Strict Gate**: If any test fails, **STOP**. Do NOT commit or push broken code.
   - Follow the `regression-safety` workflow: triage, fix the failure immediately, re-run tests until 100% pass rate is achieved.
   - Only once all tests pass with 0 failures, proceed to Step 2.

### Step 2: Clean Staging & Secrets Check
1. Run `git status` to inspect modified, untracked, and deleted files.
2. Verify that **NO** sensitive or temporary files are staged:
   - Never stage `.env` files, plaintext secrets, API keys, or private certificates.
   - Ensure temporary build artifacts (`.terraform/`, `node_modules/`, `__pycache__/`, `.pytest_cache/`) are ignored by `.gitignore`.
3. Stage intended files:
   ```bash
   git add <modified_files>
   # or
   git add .
   ```

### Step 3: Conventional Commit Creation
Create a descriptive commit following Conventional Commits format:
```bash
git commit -m "<type>(<scope>): <concise description of what was changed and verified>"
```
- Standard types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`.
- Example: `git commit -m "feat(billing): add usage quota enforcement and pass all 115 tests"`

### Step 4: Push to Remote & Verify Sync
1. Detect active branch:
   ```bash
   git branch --show-current
   ```
2. Push to the remote origin:
   ```bash
   git push origin <current_branch>
   ```
   *(If release tags were created, also push the tag: `git push origin <tag_name>`)*
3. Verify that the remote is updated and working tree is clean:
   ```bash
   git status
   ```
   Confirm output states: `"Your branch is up to date with 'origin/<branch>'."` and `"nothing to commit, working tree clean"`.
4. Inform the user of the successful push with the commit hash, branch name, and remote URL.
