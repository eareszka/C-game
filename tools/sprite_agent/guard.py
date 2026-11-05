"""Hook for the nes-sprite-artist agent: it may read its job folder, write draw.py there and run the checker. Nothing else.

Read from stdin as a PreToolUse hook. Exit code 2 refuses the call and tells the agent why.
"""
import json
import os
import re
import sys

ROOT = os.environ.get('CLAUDE_PROJECT_DIR') or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
JOBS = os.path.normcase(os.path.normpath(os.path.join(ROOT, 'art', 'enemies', 'nes')))


def refuse(why):
    print(why, file=sys.stderr)
    sys.exit(2)


def main():
    call = json.load(sys.stdin)
    tool, given = call.get('tool_name'), call.get('tool_input') or {}
    if tool == 'Bash':
        if not re.fullmatch(r'python -B tools/sprite_agent/check\.py \d{1,3}', (given.get('command') or '').strip()):
            refuse('This agent may only run: python -B tools/sprite_agent/check.py ID')
        return
    if tool in ('Read', 'Write', 'Edit'):
        path = given.get('file_path') or ''
        full = os.path.normcase(os.path.normpath(os.path.join(ROOT, path)))
        rel = os.path.relpath(full, JOBS) if full.startswith(JOBS + os.sep) else None
        parts = rel.split(os.sep) if rel else []
        if len(parts) != 2 or not re.match(r'\d{2,3}_', parts[0]):
            refuse('This agent may only use files directly inside its own job folder.')
        if tool != 'Read' and parts[1] != 'draw.py':
            refuse('This agent may only write draw.py.')
        return
    refuse('This agent may only use Read, Write, Edit and the checker.')


if __name__ == '__main__':
    main()
