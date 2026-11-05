"""Draws one sprite with a brand-new Claude. It knows only the fixed prompt, the fixed rule and this enemy's brief.

    python -B tools/sprite_agent/run.py 87
    python -B tools/sprite_agent/run.py 87 --codex

Each run is its own process: no chat history, memory, skills, MCP servers, user settings or saved session. A hook
(guard.py) limits it to its job folder, writing draw.py and running the checker. Nothing is installed in the game.
The whole run is logged to agent_log.jsonl in the job folder, and this prints which files it opened.

With --codex the sprite is drawn by a brand-new Codex instead, given the same PROMPT.md and the same job folder and checked
by the same checker. It has no user config, hooks, plugins, memories, project docs or saved session, and its sandbox lets it
write only inside the job folder. It differs in one way: the sandbox stops writes but not reads, and it can run other
commands in there, so run_codex prints every command it ran, to show if it strayed.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
import new_job

MODEL = 'opus'
EFFORT = 'high'
TIME_LIMIT = 45 * 60              # seconds; a run that's still going by then is stopped and counts as failed


def command(message, model=MODEL, effort=EFFORT, prompt=None):
    return [shutil.which('claude'), '-p', message,
            '--system-prompt-file', prompt or os.path.join(HERE, 'PROMPT.md'),
            '--tools', 'Read,Write,Edit,Bash',
            '--allowedTools', 'Read', 'Write', 'Edit', 'Bash(python -B tools/sprite_agent/check.py *)',
            '--permission-mode', 'dontAsk',
            '--settings', os.path.join(HERE, 'settings.json'),
            '--setting-sources', 'project',
            '--strict-mcp-config',
            '--disable-slash-commands',
            '--no-session-persistence',
            '--model', model, '--effort', effort,
            '--output-format', 'stream-json', '--verbose']


def clean_env():
    env = dict(os.environ, CLAUDE_CODE_DISABLE_AUTO_MEMORY='1')
    env.pop('CLAUDE_PROJECT_DIR', None)
    return env


def draw(i, who='claude'):
    os.chdir(ROOT)
    folder = new_job.make(i)
    return run_codex(i, folder) if who == 'codex' else run_agent(i, folder)


CHECK_SHIM = '''"""Runs the real checker, so the fixed prompt's command works from this job folder, the only place Codex can write."""
import subprocess
import sys
sys.exit(subprocess.run([sys.executable, '-B', %r] + sys.argv[1:]).returncode)
'''


def codex_command(reply_path):
    return [shutil.which('codex'), 'exec', '-', '--json', '--ephemeral', '--ignore-user-config', '--ignore-rules', '--skip-git-repo-check',
            '--disable', 'hooks', '--disable', 'plugins', '--disable', 'apps', '--disable', 'memories', '--disable', 'multi_agent', '--disable', 'image_generation',
            '-s', 'workspace-write', '-o', reply_path,
            '-c', 'model_reasoning_effort=high', '-c', 'project_doc_max_bytes=0', '-c', 'windows.sandbox=elevated', '-c', 'web_search=disabled']


def run_codex(i, folder):
    """One brand-new Codex on one job folder, with the fixed PROMPT.md and the same message a Claude agent gets."""
    os.chdir(ROOT)
    folder = os.path.abspath(folder)
    job_path = os.path.join(folder, 'job.json')
    with open(job_path, encoding='utf-8') as f:
        job = json.load(f)
    job['agent'] = 'codex'
    with open(job_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(job, f, indent=0)
    shim_dir = os.path.join(folder, 'tools', 'sprite_agent')
    os.makedirs(shim_dir, exist_ok=True)
    with open(os.path.join(shim_dir, 'check.py'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(CHECK_SHIM % os.path.join(HERE, 'check.py'))
    with open(os.path.join(HERE, 'PROMPT.md'), encoding='utf-8') as f:
        prompt = f.read()
    message = '%s\n\nJob %d. Folder: %s/' % (prompt, i, folder.replace(os.sep, '/'))
    handle, reply_path = tempfile.mkstemp(prefix='codex_reply_', suffix='.txt')
    os.close(handle)
    log_path = os.path.join(folder, 'agent_log.jsonl')
    try:
        with open(log_path, 'w', encoding='utf-8', newline='\n') as log:
            try:
                code = subprocess.run(codex_command(reply_path), cwd=folder, input=message, stdout=log, stderr=subprocess.STDOUT, text=True, encoding='utf-8', timeout=TIME_LIMIT).returncode
            except subprocess.TimeoutExpired:
                code = 124
        with open(reply_path, encoding='utf-8', errors='replace') as f:
            reply = f.read().strip()
    finally:
        os.remove(reply_path)
    commands, kinds = [], {}
    with open(log_path, encoding='utf-8', errors='replace') as f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            item = d.get('item') or {}
            if d.get('type') == 'item.completed' and item.get('type'):
                kinds[item['type']] = kinds.get(item['type'], 0) + 1
                if item['type'] == 'command_execution' and item.get('command') not in commands:
                    commands.append(item.get('command'))
    print('Job %d finished, exit code %d.' % (i, code))
    print('Tools used:', kinds)
    print('Commands it ran:')
    for c in commands:
        print('   ', str(c)[:170])
    print(reply, flush=True)
    if code == 0 and reply:
        with open(os.path.join(folder, 'agent_reply.txt'), 'w', encoding='utf-8', newline='\n') as f:
            f.write(reply + '\n')
    return code


def run_agent(i, folder, prompt=None):
    """One brand-new agent on one job folder, with one fixed prompt (PROMPT.md unless given)."""
    os.chdir(ROOT)
    folder = os.path.abspath(folder)
    message = 'Job %d. Folder: %s/' % (i, folder.replace(os.sep, '/'))
    log_path = os.path.join(folder, 'agent_log.jsonl')
    with open(log_path, 'w', encoding='utf-8', newline='\n') as log:
        try:
            code = subprocess.run(command(message, prompt=prompt), cwd=ROOT, env=clean_env(), stdout=log, stderr=subprocess.STDOUT, text=True, encoding='utf-8', timeout=TIME_LIMIT).returncode
        except subprocess.TimeoutExpired:
            code = 124
    opened, tools, reply = [], {}, ''
    with open(log_path, encoding='utf-8') as f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get('type') == 'assistant':
                for block in d.get('message', {}).get('content', []) or []:
                    if block.get('type') == 'tool_use':
                        tools[block['name']] = tools.get(block['name'], 0) + 1
                        path = (block.get('input') or {}).get('file_path')
                        if block['name'] == 'Read' and path and os.path.basename(path) not in opened:
                            opened.append(os.path.basename(path))
            if d.get('type') == 'result':
                reply = d.get('result') or ''
    print('Job %d finished, exit code %d.' % (i, code))
    print('Tools used:', tools)
    print('Files it opened:', opened)
    print(reply, flush=True)
    if code == 0 and reply:
        with open(os.path.join(folder, 'agent_reply.txt'), 'w', encoding='utf-8', newline='\n') as f:
            f.write(reply + '\n')
    return code


if __name__ == '__main__':
    sys.exit(draw(int(sys.argv[1]), 'codex' if '--codex' in sys.argv else 'claude'))
