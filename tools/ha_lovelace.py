#!/usr/bin/env python3
"""Odczyt / zapis dashboardu Home Assistant (tryb „storage”, edytowany w UI) przez API WebSocket — to samo,
co robi edytor surowej konfiguracji. Bez restartu HA i bez podmiany plików w /config/.storage.

  ha_lovelace.py list                              — lista dashboardów (url_path, tytuł, tryb)
  ha_lovelace.py get  <url_path> [plik.yaml]        — pobranie konfiguracji (domyślnie na stdout)
  ha_lovelace.py save <url_path> <plik.yaml>        — zapis; PRZED zapisem kopia bieżącej wersji do backups/
  ha_lovelace.py views <url_path>                   — lista widoków (indeks, path, tytuł, typ)
  ha_lovelace.py save-view <url_path> <path> <plik> — podmiana jednego widoku (kopia całości przed zapisem)
  ha_lovelace.py entities [wzorzec regex]           — encje (entity_id, stan) pasujące do wzorca

Token długoterminowy HA czytany z pliku (domyślnie ~/.config/ha/token, prawa 0600) — nigdy z argumentów.
Adres: zmienna HA_URL (domyślnie http://192.168.30.20:8123).
"""

from __future__ import annotations

import asyncio
import datetime as dt
import json
import os
import re
import stat
import sys
from pathlib import Path

import websockets
import yaml

HA_URL = os.environ.get("HA_URL", "http://192.168.30.20:8123")
TOKEN_FILE = Path(os.environ.get("HA_TOKEN_FILE", Path.home() / ".config/ha/token"))
BACKUP_DIR = Path(os.environ.get("HA_BACKUP_DIR", Path.home() / "ha-backups"))


def token() -> str:
    st = TOKEN_FILE.stat()
    if st.st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        sys.exit(f"{TOKEN_FILE}: prawa zbyt szerokie (chmod 600)")
    return TOKEN_FILE.read_text().strip()


class HA:
    def __init__(self):
        self.ws = None
        self.n = 0

    async def __aenter__(self):
        url = re.sub(r"^http", "ws", HA_URL.rstrip("/")) + "/api/websocket"
        self.ws = await websockets.connect(url, max_size=32 * 1024 * 1024)
        hello = json.loads(await self.ws.recv())
        assert hello["type"] == "auth_required", hello
        await self.ws.send(json.dumps({"type": "auth", "access_token": token()}))
        res = json.loads(await self.ws.recv())
        if res["type"] != "auth_ok":
            sys.exit(f"logowanie do HA nieudane: {res.get('message', res['type'])}")
        return self

    async def __aexit__(self, *a):
        await self.ws.close()

    async def call(self, **msg):
        self.n += 1
        msg["id"] = self.n
        await self.ws.send(json.dumps(msg))
        while True:
            r = json.loads(await self.ws.recv())
            if r.get("id") == self.n and r.get("type") == "result":
                if not r["success"]:
                    raise RuntimeError(r.get("error"))
                return r["result"]


def url_arg(p: str):
    return None if p in ("-", "default", "lovelace") else p


async def main(argv):
    if not argv:
        sys.exit(__doc__)
    cmd = argv[0]
    async with HA() as ha:
        if cmd == "list":
            for d in await ha.call(type="lovelace/dashboards/list"):
                print(f"{d.get('url_path')}\t{d.get('title')}\t{d.get('mode')}")
        elif cmd == "get":
            cfg = await ha.call(type="lovelace/config", url_path=url_arg(argv[1]))
            out = yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False, width=120)
            if len(argv) > 2:
                Path(argv[2]).write_text(out, encoding="utf-8")
                print(f"zapisano {argv[2]}")
            else:
                print(out)
        elif cmd == "save":
            new = yaml.safe_load(Path(argv[2]).read_text(encoding="utf-8"))
            if not isinstance(new, dict) or "views" not in new:
                sys.exit("plik nie wygląda na konfigurację dashboardu (brak 'views')")
            cur = await ha.call(type="lovelace/config", url_path=url_arg(argv[1]))
            BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            bak = BACKUP_DIR / f"{argv[1]}-{dt.datetime.now():%Y%m%d-%H%M%S}.yaml"
            bak.write_text(yaml.safe_dump(cur, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8")
            await ha.call(type="lovelace/config/save", url_path=url_arg(argv[1]), config=new)
            print(f"zapisano dashboard '{argv[1]}' (kopia poprzedniej wersji: {bak})")
        elif cmd == "views":
            cfg = await ha.call(type="lovelace/config", url_path=url_arg(argv[1]))
            for i, v in enumerate(cfg.get("views", [])):
                print(f"{i}\t{v.get('path')}\t{v.get('title')}\t{v.get('type', 'masonry')}")
        elif cmd == "save-view":
            # save-view <url_path> <ścieżka widoku> <plik.yaml z jednym widokiem>
            view = yaml.safe_load(Path(argv[3]).read_text(encoding="utf-8"))
            if not isinstance(view, dict) or not ("cards" in view or "sections" in view):
                sys.exit("plik nie wygląda na widok (brak 'cards'/'sections')")
            cur = await ha.call(type="lovelace/config", url_path=url_arg(argv[1]))
            idx = [i for i, v in enumerate(cur.get("views", [])) if v.get("path") == argv[2]]
            if len(idx) != 1:
                sys.exit(f"widok '{argv[2]}' nie znaleziony jednoznacznie ({len(idx)})")
            BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            bak = BACKUP_DIR / f"{argv[1]}-{dt.datetime.now():%Y%m%d-%H%M%S}.yaml"
            bak.write_text(yaml.safe_dump(cur, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8")
            view.setdefault("path", argv[2])
            new = dict(cur)
            new["views"] = list(cur["views"])
            new["views"][idx[0]] = view
            await ha.call(type="lovelace/config/save", url_path=url_arg(argv[1]), config=new)
            print(f"zapisano widok '{argv[2]}' w '{argv[1]}' (kopia całości: {bak})")
        elif cmd == "entities":
            pat = re.compile(argv[1] if len(argv) > 1 else ".")
            for s in await ha.call(type="get_states"):
                if pat.search(s["entity_id"]):
                    print(f"{s['entity_id']}\t{s['state']}")
        else:
            sys.exit(__doc__)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
