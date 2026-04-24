import json
import os
import sys
import webbrowser
from dataclasses import dataclass, field

TOKEN_GENERATOR_URL = "https://twitchtokengenerator.com/quick/a9IivPUewe"

DEFAULT_VRC_OSC_HOST = "127.0.0.1"
DEFAULT_VRC_OSC_PORT = 9000


@dataclass
class Config:
    twitch_token: str
    twitch_channel: str
    vrc_osc_host: str
    vrc_osc_port: int
    blocked_bots: set[str] = field(default_factory=set)
    blocked_prefixes: set[str, ...] = field(default_factory=set)


def _config_path() -> str:
    base = (
        sys.executable if getattr(sys, "frozen", False) else __file__
    )
    return os.path.join(os.path.dirname(base), "config.json")


def load_config() -> Config:
    path = _config_path()
    token = ""

    if os.path.exists(path):
        with open(path) as f:
            cfg = json.load(f)

        token = cfg.get("twitch_token", "")
        channel = cfg.get("twitch_channel", "")
        blocked_bots = cfg.get("blocked_bots", [])
        blocked_prefixes = cfg.get("blocked_prefixes", [])
        vrc_osc_host = cfg.get("vrc_osc_host", DEFAULT_VRC_OSC_HOST)
        vrc_osc_port = cfg.get("vrc_osc_port", DEFAULT_VRC_OSC_PORT)

        if not isinstance(vrc_osc_host, str):
            vrc_osc_host = DEFAULT_VRC_OSC_HOST
        if not isinstance(vrc_osc_port, int):
            vrc_osc_port = DEFAULT_VRC_OSC_PORT

        if token and channel:
            cfg_changed = False
            for key, value in [
                ("blocked_bots", blocked_bots),
                ("blocked_prefixes", blocked_prefixes),
                ("vrc_osc_host", vrc_osc_host),
                ("vrc_osc_port", vrc_osc_port),
            ]:
                if key not in cfg:
                    cfg[key] = value
                    cfg_changed = True
            if cfg_changed:
                with open(path, "w") as f:
                    json.dump(cfg, f, indent=2)

            return Config(
                twitch_token=token,
                twitch_channel=channel,
                vrc_osc_host=vrc_osc_host,
                vrc_osc_port=vrc_osc_port,
                blocked_bots={u.strip().lower() for u in blocked_bots if u.strip()},
                blocked_prefixes=tuple(
                    p for p in (x.strip() for x in blocked_prefixes) if p
                ),
            )

        print("Invalid config, please re-enter the required information.")

    if not token:
        try:
            webbrowser.open(TOKEN_GENERATOR_URL, new=2)
            print(f"Please generate a Twitch token at: {TOKEN_GENERATOR_URL}")
        except Exception:
            print("Could not open your browser automatically.")

    print("──────────────────────── First-run setup ────────────────────────")
    print(f"Generate a token at {TOKEN_GENERATOR_URL}")
    print("Required scope: chat:read\n")
    token = input("Paste your access token: ").strip()
    channel = input("Twitch channel name to watch: ").strip().lower()

    if not token.startswith("oauth:"):
        token = "oauth:" + token

    with open(path, "w") as f:
        json.dump(
            {
                "twitch_token": token,
                "twitch_channel": channel,
                "vrc_osc_host": DEFAULT_VRC_OSC_HOST,
                "vrc_osc_port": DEFAULT_VRC_OSC_PORT,
                "blocked_bots": [],
                "blocked_prefixes": [],
            },
            f,
            indent=2
        )
    print(f"\nConfig saved to {path}\n")

    return Config(
        twitch_token=token,
        twitch_channel=channel,
        vrc_osc_host=DEFAULT_VRC_OSC_HOST,
        vrc_osc_port=DEFAULT_VRC_OSC_PORT,
        blocked_bots=set(),
        blocked_prefixes=tuple(),
    )
