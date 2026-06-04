#!/usr/bin/env python3
import sys
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Graft disconnected git branches into a linear history via fast-export/import streams.")
    parser.add_argument("--branches", required=True, help="Comma-separated list of branch names in order of dependency/chronology (e.g. 'develop,staging,master')")
    parser.add_argument("--graft", action="append", default=[], help="Graft connection in 'child_original_oid:parent_original_oid' format (can be specified multiple times)")
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Parse branches
    branch_order = [b.strip().encode('utf-8') for b in args.branches.split(',')]
    
    # Parse grafts: child_oid -> parent_oid
    grafts = {}
    target_oids = set()
    for g in args.graft:
        if ":" not in g:
            print(f"Error: Invalid graft format '{g}'. Must be child_oid:parent_oid", file=sys.stderr)
            sys.exit(1)
        child, parent = g.split(":")
        child_bytes = child.strip().encode('utf-8')
        parent_bytes = parent.strip().encode('utf-8')
        grafts[child_bytes] = parent_bytes
        target_oids.add(child_bytes)
        target_oids.add(parent_bytes)

    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer

    commit_lines = []
    in_blob = False

    # 1. First Pass: Stream blobs immediately, buffer commits
    while True:
        line = stdin.readline()
        if not line:
            break

        if line.startswith(b"blob\n") or line.startswith(b"blob "):
            in_blob = True

        if in_blob:
            stdout.write(line)
            if line.startswith(b"data "):
                size = int(line.split()[1])
                stdout.write(stdin.read(size))
                nl = stdin.readline() # Blobs have a separator newline
                stdout.write(nl)
                in_blob = False
        else:
            commit_lines.append(line)
            if line.startswith(b"data "):
                size = int(line.split()[1])
                commit_lines.append(stdin.read(size))

    # 2. Extract mark numbers for target OIDs
    oid_to_mark = {}
    current_mark = None
    in_commit = False

    idx = 0
    while idx < len(commit_lines):
        item = commit_lines[idx]
        if item.startswith(b"commit "):
            in_commit = True
            current_mark = None
        elif item.startswith(b"reset ") or item.startswith(b"tag "):
            in_commit = False
            current_mark = None
        elif item.startswith(b"mark "):
            current_mark = item.split()[1]
        elif item.startswith(b"original-oid "):
            oid = item.split()[1]
            if in_commit and oid in target_oids:
                oid_to_mark[oid] = current_mark
        elif item.startswith(b"data "):
            idx += 1
        idx += 1

    print(f"Debug: Found OID marks: {oid_to_mark}", file=sys.stderr)

    # 3. Parse commits into command blocks
    blocks = []
    current_block = []
    idx = 0
    while idx < len(commit_lines):
        line = commit_lines[idx]
        is_new_block = False
        if (line.startswith(b"commit ") or 
            line.startswith(b"reset ") or 
            line.startswith(b"tag ") or 
            line.startswith(b"alias") or 
            line.startswith(b"checkpoint") or 
            line.startswith(b"progress") or 
            line.startswith(b"feature") or 
            line.startswith(b"option") or 
            line.startswith(b"done")):
            is_new_block = True

        if is_new_block and current_block:
            blocks.append(current_block)
            current_block = []

        current_block.append(line)
        if line.startswith(b"data "):
            current_block.append(commit_lines[idx+1])
            idx += 1
        idx += 1

    if current_block:
        blocks.append(current_block)

    # 4. Classify blocks for topological reordering
    header_blocks = []
    branch_blocks = {b: [] for b in branch_order}
    tag_blocks = []
    misc_blocks = []

    for block in blocks:
        first_line = block[0]
        if (first_line.startswith(b"feature") or 
            first_line.startswith(b"option") or 
            first_line.startswith(b"alias") or 
            first_line.startswith(b"checkpoint")):
            header_blocks.append(block)
        elif first_line.startswith(b"tag "):
            tag_blocks.append(block)
        else:
            # Check if it belongs to one of the ordered branches
            matched = False
            for b in branch_order:
                if first_line.startswith(b"commit refs/heads/" + b) or first_line.startswith(b"reset refs/heads/" + b):
                    branch_blocks[b].append(block)
                    matched = True
                    break
            if not matched:
                misc_blocks.append(block)

    # 5. Process blocks (graft 'from' commands on branch root commits)
    def process_block(block):
        new_block = []
        in_commit = False
        grafted_parent_mark = None
        idx = 0
        while idx < len(block):
            item = block[idx]
            new_block.append(item)
            if item.startswith(b"commit "):
                in_commit = True
                grafted_parent_mark = None
            elif item.startswith(b"original-oid "):
                oid = item.split()[1]
                if in_commit and oid in grafts:
                    parent_oid = grafts[oid]
                    grafted_parent_mark = oid_to_mark.get(parent_oid)
            elif item.startswith(b"data "):
                new_block.append(block[idx+1])
                if in_commit and grafted_parent_mark:
                    new_block.append(b"from " + grafted_parent_mark + b"\n")
                idx += 1
            idx += 1
        return new_block

    # Reassemble blocks in correct order
    out_blocks = header_blocks
    
    # Append sorted branches
    for b in branch_order:
        for block in branch_blocks[b]:
            out_blocks.append(process_block(block))
            
    # Append misc branches
    for block in misc_blocks:
        out_blocks.append(process_block(block))
        
    # Append tags last
    out_blocks.extend(tag_blocks)

    # 6. Output final stream
    for block in out_blocks:
        for line in block:
            stdout.write(line)

if __name__ == "__main__":
    main()
