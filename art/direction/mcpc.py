"""Minimal stdio MCP client for the pixel-plugin's pixel-mcp server.

    from mcpc import Pixel
    px = Pixel(); px.call("create_canvas", width=16, height=16)
"""
import json, os, subprocess, sys

EXE = os.environ.get("PIXEL_MCP_EXE", os.path.expanduser("~/.claude/plugins/cache/pixel-plugin/pixel-plugin/0.5.0/bin/pixel-mcp-windows-amd64.exe"))
CFG = os.environ.get("PIXEL_MCP_CONFIG", os.path.expanduser("~/.config/pixel-mcp/config.json"))


class Pixel:
    def __init__(self):
        env = dict(os.environ, PIXEL_MCP_CONFIG=CFG)
        self.p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, env=env)
        self.n = 0
        self.rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                "clientInfo": {"name": "mcpc", "version": "0"}})
        self.send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def send(self, msg):
        self.p.stdin.write((json.dumps(msg) + "\n").encode("utf-8"))
        self.p.stdin.flush()

    def rpc(self, method, params=None):
        self.n += 1
        self.send({"jsonrpc": "2.0", "id": self.n, "method": method, "params": params or {}})
        while True:
            line = self.p.stdout.readline()
            if not line:
                raise RuntimeError("server closed")
            msg = json.loads(line.decode("utf-8"))
            if msg.get("id") == self.n:
                if "error" in msg:
                    raise RuntimeError(msg["error"])
                return msg["result"]

    def tools(self):
        return self.rpc("tools/list")["tools"]

    def call(self, name, **args):
        r = self.rpc("tools/call", {"name": name, "arguments": args})
        text = "".join(c.get("text", "") for c in r.get("content", []))
        if r.get("isError"):
            raise RuntimeError(f"{name}: {text}")
        try:
            return json.loads(text)
        except Exception:
            return text


if __name__ == "__main__":
    px = Pixel()
    for t in px.tools():
        props = t.get("inputSchema", {}).get("properties", {})
        req = t.get("inputSchema", {}).get("required", [])
        print(t["name"], "(" + ", ".join(k + ("*" if k in req else "") for k in props) + ")")
