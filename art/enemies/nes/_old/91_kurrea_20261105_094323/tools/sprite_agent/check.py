"""Runs the real checker, so the fixed prompt's command works from this job folder, the only place Codex can write."""
import subprocess
import sys
sys.exit(subprocess.run([sys.executable, '-B', 'C:\\Users\\13178\\OneDrive - UWM\\Desktop\\projects\\C-game\\tools\\sprite_agent\\check.py'] + sys.argv[1:]).returncode)
