#!/usr/bin/env python3
import json
import os
import re
import sys

ENV_FILENAME_REGEX = re.compile(r'(^|[/\\])\.env(\.[a-zA-Z0-9_.-]+)?$')
COMMAND_ENV_REGEX = re.compile(r'(?:^|[\s;|&`$(<>])(?:\.?\/|[a-zA-Z0-9_\-\.\/]*\/)?\.env(?:\.[a-zA-Z0-9_.-]+)?(?=[\s;|&`$)<>]|$)')

def is_env_path(path: str) -> bool:
    if not path:
        return False
    basename = os.path.basename(path.rstrip('/\\'))
    return basename == ".env" or basename.startswith(".env.")

def main():
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        print(json.dumps({"decision": "allow"}))
        sys.exit(0)

    tool_call = input_data.get("toolCall", {})
    tool_name = tool_call.get("name", "")
    args = tool_call.get("args", {})

    if tool_name in ("read_file", "view_file"):
        file_path = args.get("Path") or args.get("path") or ""
        if is_env_path(file_path):
            print(json.dumps({
                "decision": "deny",
                "reason": f"BLOCKED: Access to environment file '{file_path}' is denied."
            }))
            sys.exit(0)

    if tool_name == "run_command":
        command = args.get("CommandLine") or args.get("command") or ""
        if COMMAND_ENV_REGEX.search(command):
            print(json.dumps({
                "decision": "deny",
                "reason": f"BLOCKED: Command touches .env file: '{command}'."
            }))
            sys.exit(0)

    print(json.dumps({"decision": "allow"}))
    sys.exit(0)

if __name__ == "__main__":
    main()
