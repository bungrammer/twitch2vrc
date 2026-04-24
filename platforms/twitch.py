from twitchio.ext import commands
from config import Config
from osc import manager
from platforms.base import BaseChat


def strip_emotes(content: str, emotes_tag: str | None) -> str:
    if not emotes_tag:
        return content

    ranges: list[tuple[int, int]] = []
    for emote_part in emotes_tag.split("/"):
        if ":" not in emote_part:
            continue
        _, positions = emote_part.split(":", 1)
        for pos in positions.split(","):
            if "-" not in pos:
                continue
            start, end = pos.split("-")
            ranges.append((int(start), int(end)))

    chars = list(content)
    for start, end in sorted(ranges, reverse=True):
        del chars[start:end+1]

    return " ".join("".join(chars).split())


class TwitchBot(commands.Bot, BaseChat):
    def __init__(self, config: Config) -> None:
        super().__init__(
            token=config.twitch_token,
            prefix="!",
            initial_channels=[config.twitch_channel],
        )
        self._config = config

    async def start(self) -> None:
        await super().start()

    async def stop(self) -> None:
        await self.close()

    async def event_ready(self) -> None:
        print(
            f"Twitch connect as {self.nick}"
            f"watching #{self._config.twitch_channel}"
        )

    async def event_message(self, message) -> None:
        if message.echo:
            return
        if message.author is None:
            return

        username = message.author.display_name
        content = message.content or ""

        if any(content.startswith(p) for p in self._config.blocked_prefixes):
            return
        if username.strip().lower() in self._config.blocked_bots:
            return

        emotes_tag = (message.tags or {}).get("emotes")
        content = strip_emotes(content, emotes_tag)

        if not content.strip():
            return

        print(f"[Twitch] {username}: {content}")
        manager.enqueue(username, content)
