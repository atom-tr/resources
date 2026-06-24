---
name: svn-to-git-migration
description: Migrate SVN repositories to Git, preserving history and grafting disconnected branches into a linear topological history using streaming fast-export/import.
---

# SVN to Git History Grafting Migration Skill

This skill provides a memory-efficient, fast, and robust mechanism to migrate multiple SVN branches (which represent promotions or environment steps, e.g. `develop -> staging -> master`) into a single Git repository with a connected, linear history.

## The Challenge

During SVN-to-Git migration of branches that were created as independent paths/branches in SVN, standard tools like `git svn clone` import them as separate Git repositories with **no common ancestor** (0 commits in common). 

Trying to link them via standard `git rebase` on repositories with 10k+ commits fails with endless merge conflicts. Using `git filter-branch` is extremely slow (often taking hours for medium-size repositories).

## The Solution

This skill uses a single-pass streaming re-parenting approach. It intercepts a `git fast-export` stream, dynamically parses command blocks, inserts `from <parent_mark>` pointers on the fly to graft roots to their parent branch tips, reorders the branch blocks topologically (so ancestors are imported before their descendants), and pipes the stream directly into `git fast-import`.

## Workflow Steps

### Step 0: Generate authors.txt

SVN identifies committers by simple system usernames, whereas Git requires a full name and email address. You must build an `authors.txt` file mapping the SVN usernames to Git author formats:
```text
svn_username = Full Name <email@example.com>
```

#### Steps to generate:
1.  **Extract all unique SVN usernames** from the repository logs:
    ```bash
    svn log "$SVN_URL" --quiet --non-interactive | grep -E "^r[0-9]+" | awk '{print $3}' | sort -u > /tmp/svn_users.txt
    ```
2.  **Query your corporate directory (LDAP/AD)** or generate fallsback to map each username to a Git signature:
    ```bash
    # Simple fallback script to generate authors.txt
    while read -r uid; do
      [[ -z "$uid" ]] && continue
      # Optionally run ldapsearch to retrieve full name and email, or fallback:
      name="$uid"
      email="${uid}@company.com"
      echo "${uid} = ${name} <${email}>" >> authors.txt
    done < /tmp/svn_users.txt
    ```

### Step 1: Clone SVN Branches Independently

Clone each branch from SVN using `git svn clone` into its own directory:
```bash
git svn clone "$SVN_URL/branches/develop" --no-metadata --authors-file=authors.txt /tmp/svn-migration/develop
git svn clone "$SVN_URL/production/staging" --no-metadata --authors-file=authors.txt /tmp/svn-migration/staging
git svn clone "$SVN_URL/branches/master" --no-metadata --authors-file=authors.txt /tmp/svn-migration/master
```

### Step 2: Initialize a Local Bare Git Repository and Push

Create a single bare Git repository to serve as the unified destination:
```bash
git init --bare /tmp/svn-migration/unified.git
```
Push the independent HEAD commits to the bare repository under their respective branch names:
```bash
cd /tmp/svn-migration/develop && git remote add origin /tmp/svn-migration/unified.git && git push origin HEAD:develop
cd /tmp/svn-migration/staging && git remote add origin /tmp/svn-migration/unified.git && git push origin HEAD:staging
cd /tmp/svn-migration/master  && git remote add origin /tmp/svn-migration/unified.git && git push origin HEAD:master
```

At this stage, `develop`, `staging`, and `master` exist in `unified.git` but are completely disconnected.

### Step 3: Identify Root Commits of Branches

Find the 40-character original commit hashes (OIDs) of the root (first) commits of each branch.
```bash
# Oldest commit on develop
git -C /tmp/svn-migration/develop rev-list --max-parents=0 HEAD
# Oldest commit on staging (to be grafted to the tip of develop)
git -C /tmp/svn-migration/staging rev-list --max-parents=0 HEAD
# Oldest commit on master (to be grafted to the tip of staging)
git -C /tmp/svn-migration/master rev-list --max-parents=0 HEAD
```
Let's assume:
- Develop root: `1111111111111111111111111111111111111111`
- Staging root: `2222222222222222222222222222222222222222`
- Master root: `3333333333333333333333333333333333333333`

### Step 4: Run the Streaming Graft Pipeline

Run the Python grafting script on the `fast-export` stream of the disconnected repository, and import the modified stream into a new bare repository.

```bash
# Initialize destination repository
rm -rf /tmp/svn-migration/connected.git && git init --bare /tmp/svn-migration/connected.git

# Execute streaming pipeline
git -C /tmp/svn-migration/unified.git fast-export --show-original-ids --all | \
  python3 scripts/graft.py \
    --branches develop,staging,master \
    --graft 2222222222222222222222222222222222222222:1111111111111111111111111111111111111111 \
    --graft 3333333333333333333333333333333333333333:2222222222222222222222222222222222222222 \
  | (cd /tmp/svn-migration/connected.git && git fast-import)
```

**Parameters explained:**
*   `--branches`: The order in which branches must be declared (topological dependency order). Ancestors must be declared before descendants.
*   `--graft`: `<child_original_oid>:<parent_original_oid>` mapping. This maps the root commit of a downstream branch to the root commit of its upstream branch (or any specific commit in history).

### Step 5: Perform Tip Alignment Merges (`-s ours`)

Clone the connected bare repository and align the branch tips to establish a common ancestor for future promotions:
```bash
git clone /tmp/svn-migration/connected.git /tmp/svn-migration/workspace
cd /tmp/svn-migration/workspace

# Checkout branches
git checkout -b develop origin/develop
git checkout -b staging origin/staging
git checkout -b master origin/master

# Merge develop -> staging keeping staging code intact
git checkout staging
git merge -s ours develop -m "Merge develop into staging (ours)"

# Merge staging -> master keeping master code intact
git checkout master
git merge -s ours staging -m "Merge staging into master (ours)"
```

### Step 6: Push to final target Git Server

Push the aligned branches from the workspace back to your target bare repository or remote server:
```bash
# Overwrite local bare base
git push --force /tmp/unified.git develop staging master

# Push to remote Git server
git push origin develop staging master
```

## How `graft.py` Works internally

The `scripts/graft.py` script is designed for extreme token and memory efficiency:
1.  **Streaming Blobs**: Blobs represent 99%+ of the repository size. The script streams blobs directly to `stdout` byte-by-byte without holding them in memory.
2.  **State Machine Parsing**: It tracks state transitions to safely process multi-line commit data blocks, avoiding matching command words (like `blob`) inside commit messages or filenames.
3.  **Command Block Parsing**: Commits, resets, tags, and options are parsed into discrete logical blocks in memory.
4.  **Topological Sorting**: Blocks are categorized by branch refname and reordered so that dependent branch blocks are declared sequentially, ensuring that parent marks are defined before children reference them.
5.  **Dynamic Grafting**: Commits containing targeted downstream roots have a `from <parent_mark>` instruction appended right after their commit message data block, establishing the parent relationship.

## Syncing New SVN Commits

When SVN receives new commits, you must pull them into Git. Depending on how you structured the history, use one of the following workflows:

### Workflow A: Re-Grafting (If history was rewritten)
Because the OID grafting process rewrites all commit hashes for staging/master, you cannot run `git svn rebase` directly on the rewritten repository.

Instead, you must fetch the new commits in the independent branch workspaces (which hold the clean `git-svn` metadata), check if there are actual updates, and if so, push them to the intermediate `unified.git` repository, re-run the grafting pipeline, perform the tip merges, and push the results.

> [!IMPORTANT]
> **Check for updates first**: If SVN has no new commits, you must skip the re-grafting and tip merge alignment process entirely. Running the alignment merges (`-s ours`) on unchanged branches will create redundant merge commits with new timestamps, changing the branch tip hashes and requiring unnecessary force-pushes.

#### Step 1: Fetch from SVN and check for updates
Go to each independent branch clone directory and fetch the latest commits from SVN:
```bash
cd /tmp/svn-migration/develop && git svn fetch
cd /tmp/svn-migration/staging && git svn fetch
cd /tmp/svn-migration/master  && git svn fetch
```

To verify if there are any new commits that need to be processed:
```bash
# Check if the fetched git-svn tip of all branches are already integrated in the unified target repository
# (Run this check for each branch; if all return true/exit-code-0, then no updates are found)
git -C /tmp/unified.git merge-base --is-ancestor $(git -C /tmp/svn-migration/develop rev-parse refs/remotes/git-svn) develop && \
git -C /tmp/unified.git merge-base --is-ancestor $(git -C /tmp/svn-migration/staging rev-parse refs/remotes/git-svn) staging && \
git -C /tmp/unified.git merge-base --is-ancestor $(git -C /tmp/svn-migration/master rev-parse refs/remotes/git-svn) master && \
echo "No updates found in SVN. Aborting sync process to avoid redundant merges." && exit 0
```

#### Step 2: Push the new commits to `unified.git`
Push the updated `git-svn` references from each branch clone to the intermediate `unified.git` repository, updating the target branch pointers:
```bash
cd /tmp/svn-migration/develop && git push --force origin refs/remotes/git-svn:refs/heads/develop
cd /tmp/svn-migration/staging && git push --force origin refs/remotes/git-svn:refs/heads/staging
cd /tmp/svn-migration/master  && git push --force origin refs/remotes/git-svn:refs/heads/master
```

#### Step 3: Run the Streaming Graft Pipeline
Re-run the grafting pipeline using `graft.py` (the root OIDs for grafting remain the same as the original ones):
```bash
rm -rf /tmp/svn-migration/connected.git && git init --bare /tmp/svn-migration/connected.git

git -C /tmp/svn-migration/unified.git fast-export --show-original-ids --all | \
  python3 scripts/graft.py \
    --branches develop,staging,master \
    --graft 2222222222222222222222222222222222222222:1111111111111111111111111111111111111111 \
    --graft 3333333333333333333333333333333333333333:2222222222222222222222222222222222222222 \
  | (cd /tmp/svn-migration/connected.git && git fast-import)
```

#### Step 4: Perform Tip Merges
Clone the newly connected repository, recreate the branches, and perform the tip alignment merges (`-s ours`):
```bash
rm -rf /tmp/svn-migration/new_workspace
git clone /tmp/svn-migration/connected.git /tmp/svn-migration/new_workspace
cd /tmp/svn-migration/new_workspace

# Setup local branches
git checkout -b develop origin/develop
git checkout -b staging origin/staging
git checkout -b master origin/master

# Align tips
git checkout staging
git merge -s ours develop -m "Merge develop into staging (ours)"

git checkout master
git merge -s ours staging -m "Merge staging into master (ours)"
```

#### Step 5: Push to Remote target Git Server
Push the updated branches to your target Git server using the batch push script:
```bash
scripts/push_in_batches.sh -f /tmp/svn-migration/new_workspace staging origin 200
scripts/push_in_batches.sh -f /tmp/svn-migration/new_workspace master origin 200
```

### Workflow B: Tip-Merge Alignment (Recommended for active syncing)
If you did **not** rewrite history at the roots, and instead connected the independent branch imports using `--allow-unrelated-histories` at the tips, syncing is non-destructive:
1.  **Fetch new commits** in the original git-svn workspace:
    ```bash
    cd /tmp/svn-migration/workspace
    git svn fetch --all
    ```
2.  **Push to Git server**: Push the clean branches directly to your Git server (this is a fast-forward operation, no force push needed):
    ```bash
    git push origin develop staging master
    ```
3.  **Perform standard Git merges** at the tip to align them (this is conflict-free since the common ancestor was already established):
    ```bash
    git checkout staging && git merge develop -m "Promote develop changes"
    git checkout master && git merge staging -m "Promote staging changes"
    ```

## Large Repository Push Optimization (Handling HTTP 413 / Payload Too Large)

### The Issue
When pushing a very large repository (e.g., >30,000 commits or >1GB) to a remote Git server with HTTP payload size limits (e.g., Nginx `client_max_body_size` set to 500MB), standard pushes fail with `HTTP 413` errors.

If you attempt to push in batches of commits directly to the destination branch name using force-pushing (e.g., `git push -f origin <sha>:refs/heads/<branch>`), the history's non-linear nature (parallel branches and merges) will cause subsequent batch pushes to fail:
- Force-pushing a commit on branch A overwrites the branch pointer on the remote.
- This makes any previously pushed commits on parallel branch B unreachable on the remote.
- On the next batch push, because the parent commit on branch B is no longer reachable from any advertised remote ref, the Git client cannot negotiate it as "common".
- Consequently, Git is forced to package and re-upload the entire history from scratch, resulting in a huge payload that triggers the `HTTP 413` error again.

### The Solution: Pushing via Temporary Tags
To avoid re-uploading history and prevent `HTTP 413` errors:
1. **Identify Missing Commits**: Query all remote refs (branches and tags) using `ls-remote` and retrieve only the missing commits in reverse topological order (oldest first):
   ```bash
   mapfile -t remote_shas < <(git ls-remote origin | awk '{print $1}')
   git rev-list --reverse HEAD --not "${remote_shas[@]}" > missing_commits.txt
   ```
2. **Push to Temporary Tags**: Iterate through the missing commits list and push in batches (e.g., every 200 commits) to **temporary tags** on the remote instead of the main branch:
   ```bash
   git push origin <sha>:refs/tags/temp-<branch>-<sha>
   ```
   Because tags are not overwritten, all intermediate commits remain reachable on the remote. Git negotiation will successfully identify them, keeping subsequent payload sizes minimal.
3. **Update Branch Pointer**: Once all intermediate tags are pushed, perform the final push to update the target branch:
   ```bash
   git push origin HEAD:<branch>
   ```
4. **Clean up Tags**: Delete all temporary tags on the remote in a single command:
   ```bash
   mapfile -t temp_tags < <(git ls-remote --tags origin | grep "refs/tags/temp-<branch>-" | awk '{print ":" $2}')
   if [ ${#temp_tags[@]} -gt 0 ]; then
       git push origin "${temp_tags[@]}"
   fi
   ```

A helper script implementing this logic with dynamic step scaling (binary backoff) is available at `scripts/push_in_batches.sh`.

## Real-world Migration Sync & Build Pitfalls

When syncing SVN updates to a Git repository, several common pitfalls can arise, especially around file tracking, Maven builds, and clean CI environments (like GitLab CI vs. cached Jenkins environments).

### 1. Unsynced File Deletions (Unsynced Delete Commits)
- **The Issue**: During history synchronization, if a delete commit (e.g., where files are deleted in SVN or an upstream branch) is not properly synced to the target Git repository, it causes file drift. Conversely, if files are deleted in the target repository but the corresponding SVN delete commits or history are not aligned, active files may appear to be deleted or missing in Git because the sync logic fails to map the deletion history properly.
- **The Solution**: 
  - Ensure that SVN delete commits are accurately mapped and synchronized as explicit Git commits.
  - Run comparison scripts between the raw SVN branch workspace and the Git repository to verify exact file-by-file consistency.
  - Automatically restore any active files that were incorrectly deleted during misaligned sync runs, and ensure that only genuinely deleted legacy/obsolete files in SVN are removed from Git.

### 2. CI/CD Clean Build Failures vs. Jenkins Cache
- **The Issue**: A Git commit that builds successfully on Jenkins can fail with compilation errors in GitLab CI. This is often because Jenkins runners reuse a shared local `.m2/repository` cache containing internal dependencies from other branches. A clean runner (e.g., GitLab CI) has a fresh `.m2` directory and fails to download these internal dependencies (e.g., `agency-security`, `member-security`, `member-supports`) if they are not published to the corporate Nexus mirror.
- **The Solution**:
  - Do not rely on local dependency caching for internal modules in CI.
  - Ensure all dependent modules (`member`, `partner`, etc.) are actively declared and uncommented in the parent `pom.xml` reactor so they are compiled from source during the pipeline run.
  - Ensure the pipeline runner dynamically configures `~/.m2/settings.xml` in `before_script` to point to the correct Nexus mirror.

### 3. Git Push Security Guardrails
- **The Issue**: Autonomous AI agents or scripts running in sandboxed environments may have security guardrails that block dangerous commands like `git push` to prevent accidental overwrites or data leaks.
- **The Solution**:
  - The agent should prepare, stage, and commit all changes locally (e.g., updating reactor modules in `pom.xml` or syncing source files).
  - The final `git push` command must be explicitly presented to the human user to execute manually in their terminal.



