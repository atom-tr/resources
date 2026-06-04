#!/bin/bash
# Script to push git commits in batches, automatically resuming from the remote tip
# and dynamically scaling step size (binary backoff) to avoid HTTP 413 (Payload Too Large) errors.
# Uses temporary remote tags to keep history reachable and avoid re-uploading large histories.
set -e

# Detect if force push is requested
FORCE_FLAG=""
for arg in "$@"; do
    if [ "$arg" = "-f" ] || [ "$arg" = "--force" ]; then
        FORCE_FLAG="--force"
        break
    fi
done

# Filter out force flags from positional parameters
args=()
for arg in "$@"; do
    if [ "$arg" != "-f" ] && [ "$arg" != "--force" ]; then
        args+=("$arg")
    fi
done

REPO_PATH="${args[0]}"
BRANCH="${args[1]}"
REMOTE="${args[2]:-gitlab}"
DEFAULT_STEP=${args[3]:-200}

if [ -z "$REPO_PATH" ] || [ -z "$BRANCH" ]; then
    echo "Usage: $0 [-f|--force] <repo_path> <branch> [remote] [step]"
    exit 1
fi

if [ ! -d "$REPO_PATH" ]; then
    echo "Error: Directory $REPO_PATH does not exist."
    exit 1
fi

# Fetch latest refs from remote to ensure local tracking refs are updated
echo "Fetching latest refs from remote $REMOTE..."
git -C "$REPO_PATH" fetch "$REMOTE" || true

# Get list of all remote SHAs (from branches and tags) to identify missing commits
echo "Listing remote refs on $REMOTE..."
mapfile -t remote_shas < <(git -C "$REPO_PATH" ls-remote "$REMOTE" | awk '{print $1}')

echo "Retrieving missing commits for $BRANCH in $REPO_PATH..."
if [ ${#remote_shas[@]} -gt 0 ]; then
    # Filter out all commits reachable from any remote branch/tag
    mapfile -t commits < <(git -C "$REPO_PATH" rev-list --reverse "$BRANCH" --not "${remote_shas[@]}")
else
    mapfile -t commits < <(git -C "$REPO_PATH" rev-list --reverse "$BRANCH")
fi

total=${#commits[@]}

if [ "$total" -eq 0 ]; then
    echo "All commits for branch $BRANCH are already present on remote $REMOTE."
    echo "Performing final push to ensure branch pointer is fully updated..."
    git -C "$REPO_PATH" push $FORCE_FLAG "$REMOTE" "$BRANCH"
    
    # Clean up temporary tags on the remote even if no commits were pushed in this run
    echo "Cleaning up temporary tags on remote..."
    mapfile -t temp_tags < <(git -C "$REPO_PATH" ls-remote --tags "$REMOTE" | grep "refs/tags/temp-$BRANCH-" | awk '{print ":" $2}')
    if [ ${#temp_tags[@]} -gt 0 ]; then
        echo "Deleting ${#temp_tags[@]} temporary tags on remote..."
        for ((i=0; i<${#temp_tags[@]}; i+=100)); do
            git -C "$REPO_PATH" push "$REMOTE" "${temp_tags[@]:i:100}"
        done
    fi
    echo "Cleanup completed."
    exit 0
fi

echo "Total missing commits to push: $total"

current_idx=0
step=$DEFAULT_STEP
min_step=1

while [ "$current_idx" -lt "$total" ]; do
    # Calculate target index
    target_idx=$((current_idx + step - 1))
    if [ "$target_idx" -ge "$total" ]; then
        target_idx=$((total - 1))
    fi
    
    actual_step=$((target_idx - current_idx + 1))
    sha=${commits[$target_idx]}
    
    echo "--------------------------------------------------"
    echo "Attempting to push $actual_step commits ($((current_idx + 1)) to $((target_idx + 1)) of $total) up to $sha (step size: $step)..."
    
    # Push to a temporary tag on the remote instead of the main branch
    # This keeps intermediate commits reachable on the remote so they are advertised in negotiation
    set +e
    git -C "$REPO_PATH" push "$REMOTE" "$sha:refs/tags/temp-$BRANCH-$sha"
    push_status=$?
    set -e
    
    if [ $push_status -eq 0 ]; then
        echo "Success: Pushed up to commit $((target_idx + 1))/$total ($sha)."
        current_idx=$((target_idx + 1))
        
        # Additive increase: slowly increase step size back up to the default step size
        if [ "$step" -lt "$DEFAULT_STEP" ]; then
            step=$((step * 2))
            [ "$step" -gt "$DEFAULT_STEP" ] && step=$DEFAULT_STEP
            echo "Increasing step size to $step for the next batch."
        fi
    else
        echo "Warning: Push failed for batch of $actual_step commits."
        if [ "$actual_step" -le "$min_step" ]; then
            echo "Error: Cannot push even a single commit. The commit $sha itself might contain files exceeding the remote size limits."
            exit 1
        fi
        # Multiplicative decrease: halve the step size and retry the same current_idx
        step=$((actual_step / 2))
        [ "$step" -lt 1 ] && step=1
        echo "Reducing step size to $step and retrying from commit $((current_idx + 1))..."
    fi
done

# Perform final push to ensure the branch pointer is completely updated
echo "--------------------------------------------------"
echo "Performing final push to ensure branch pointer is fully updated..."
git -C "$REPO_PATH" push $FORCE_FLAG "$REMOTE" "$BRANCH"
echo "Successfully pushed branch $BRANCH to $REMOTE."

# Clean up temporary tags on the remote
echo "Cleaning up temporary tags on remote..."
mapfile -t temp_tags < <(git -C "$REPO_PATH" ls-remote --tags "$REMOTE" | grep "refs/tags/temp-$BRANCH-" | awk '{print ":" $2}')
if [ ${#temp_tags[@]} -gt 0 ]; then
    echo "Deleting ${#temp_tags[@]} temporary tags on remote..."
    # Push in batches of 100 deletes to avoid command line length limits
    for ((i=0; i<${#temp_tags[@]}; i+=100)); do
        git -C "$REPO_PATH" push "$REMOTE" "${temp_tags[@]:i:100}"
    done
fi
echo "Cleanup completed."
