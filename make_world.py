"""Builds the Minecraft Java 1.20.1 world from build.py's commands using a real server.

Usage: python make_world.py <server.jar> <workdir>
Needs java on PATH and the nbtlib package. Starting the server accepts the Minecraft EULA.
"""
import gzip
import io
import json
import math
import shutil
import subprocess
import sys
import time
import zlib
from pathlib import Path

import nbtlib

NAME = "Muraveynik Gym"
jar, work = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
srv = work / "srv"
shutil.rmtree(srv, ignore_errors=True)
srv.mkdir(parents=True)
(srv / "eula.txt").write_text("eula=true\n")
(srv / "server.properties").write_text(
    "level-type=minecraft\\:flat\ngenerate-structures=false\ngamemode=creative\ndifficulty=peaceful\n"
    "online-mode=false\nspawn-protection=0\nmax-tick-time=-1\nview-distance=6\nlevel-name=world\n"
)
cmds = (work / "commands.txt").read_text().split("\n")[:-1]
model = json.loads((work / "model.json").read_text())

log = open(work / "server.log", "w")
p = subprocess.Popen(["java", "-Xmx3G", "-jar", str(jar), "nogui"], cwd=srv, stdin=subprocess.PIPE,
                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def wait_for(marker):
    for line in p.stdout:
        log.write(line)
        if marker in line:
            return
    raise SystemExit(f"server exited before '{marker}'")


def send(*lines):
    p.stdin.write("\n".join(lines) + "\n")
    p.stdin.flush()


wait_for("Done (")
send("forceload add -24 -10 136 71", "gamerule doMobSpawning false", "gamerule doWeatherCycle false",
     "gamerule spawnRadius 0", "weather clear", "say CHUNKS_REQUESTED")
wait_for("CHUNKS_REQUESTED")
time.sleep(15)
send(*cmds)
send("forceload remove all", "setworldspawn 120 -60 62 135", "time set 1000", "save-all flush", "say BUILD_DONE")
wait_for("BUILD_DONE")
send("stop")
for line in p.stdout:
    log.write(line)
p.wait()
log.close()

text = (work / "server.log").read_text()
filled = sum(int(l.rsplit("filled ", 1)[1].split()[0]) for l in text.splitlines() if "Successfully filled" in l)
print("commands sent:", len(cmds), "| fills reported:", text.count("Successfully filled"), "| blocks filled:", filled)

# ---- tidy the save for single-player use
world = srv / "world"
for junk in ("session.lock", "DIM-1", "DIM1", "playerdata", "stats", "advancements"):
    q = world / junk
    shutil.rmtree(q) if q.is_dir() else q.unlink(missing_ok=True)
level = nbtlib.load(world / "level.dat")
level["Data"]["LevelName"] = nbtlib.String(NAME)
level["Data"]["allowCommands"] = nbtlib.Byte(1)
level.save()
(world / "level.dat_old").unlink(missing_ok=True)


# ---- read every placed block back from the region files and compare with the model
def chunk_blocks(nbt):
    out = {}
    cx, cz = int(nbt["xPos"]), int(nbt["zPos"])
    for sec in nbt["sections"]:
        bs = sec.get("block_states")
        if not bs:
            continue
        pal = bs["palette"]
        data = bs.get("data")
        bits = max(4, math.ceil(math.log2(len(pal)))) if len(pal) > 1 else 0
        per = 64 // bits if bits else 0
        for i in range(4096):
            idx = (int(data[i // per]) & (2**64 - 1)) >> (bits * (i % per)) & (2**bits - 1) if bits else 0
            e = pal[idx]
            if e["Name"] != "minecraft:air":
                out[(cx * 16 + i % 16, int(sec["Y"]) * 16 + i // 256, cz * 16 + i // 16 % 16)] = e
    return out


saved = {}
for f in (world / "region").glob("*.mca"):
    raw = f.read_bytes()
    for i in range(1024):
        off = int.from_bytes(raw[i * 4:i * 4 + 3], "big") * 4096
        if off:
            n = int.from_bytes(raw[off:off + 4], "big")
            body = raw[off + 5:off + 4 + n]
            body = zlib.decompress(body) if raw[off + 4] == 2 else gzip.decompress(body)
            saved.update(chunk_blocks(nbtlib.File.parse(io.BytesIO(body))))
bad = []
for x, y, z, b in model:
    name, _, props = b.partition("[")
    want = dict(kv.split("=") for kv in props.rstrip("]").split(",")) if props else {}
    got = saved.get((x, y, z))
    if not got or got["Name"] != "minecraft:" + name or any(str(got["Properties"][k]) != v for k, v in want.items()):
        bad.append((x, y, z, b, got and str(got["Name"])))
print("model blocks:", len(model), "| mismatches in saved world:", len(bad), bad[:10])
pane = saved[(4, -55, 46)]
print("sample window pane state:", dict(pane["Properties"]))

dest = work / NAME
shutil.rmtree(dest, ignore_errors=True)
shutil.copytree(world, dest)
shutil.make_archive(str(work / "Muraveynik-Gym-world"), "zip", work, NAME)
print("zip:", (work / "Muraveynik-Gym-world.zip").stat().st_size, "bytes")
if bad or filled != len(model):
    sys.exit(1)
