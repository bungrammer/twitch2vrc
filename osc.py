import asyncio
import time
from pythonosc import udp_client

MAX_CHARS = 144

T_MIN_DISPLAY = 8.0
T_REFRESH = 0.1
T_OSC_RATE_LIMIT = 1.5

_osc: udp_client.SimpleUDPClient | None = None


def init_osc(host: str, port: int) -> None:
    global _osc
    _osc = udp_client.SimpleUDPClient(host, port)


def send_chatbox(text: str) -> None:
    if _osc is None:
        raise RuntimeError("OSC client not initialized")

    _osc.send_message("/chatbox/input", [text, True])


def split_text(username: str, message: str) -> list[str]:
    prefix = f"{username[:MAX_CHARS-100]}: "
    max_chunk = MAX_CHARS - len(prefix)

    words = message.split()
    blocks = []
    chunk = ""

    for word in words:
        if not chunk:
            chunk = word
        elif len(chunk) + 1 + len(word) <= max_chunk:
            chunk += " " + word
        else:
            blocks.append(prefix + chunk)
            chunk = word

    if chunk:
        blocks.append(prefix + chunk)

    return blocks if blocks else [prefix.rstrip()]


class DisplayItem:
    def __init__(self, text: str) -> None:
        self.text = text
        self._shown_at: float | None = None

    def mark_shown(self) -> None:
        if self._shown_at is None:
            self._shown_at = time.monotonic()

    @property
    def age(self) -> float:
        return (
            time.monotonic() - self._shown_at
            if self._shown_at else 0.0
        )

    @property
    def can_be_removed(self) -> bool:
        return self._shown_at is not None and self.age >= T_MIN_DISPLAY


class DisplayManager:
    MAX_QUEUE_SIZE = 25

    def __init__(self) -> None:
        self.queue: list[DisplayItem] = []
        self.active: list[DisplayItem] = []

    def enqueue(self, username: str, message: str) -> None:
        if len(self.queue) >= self.MAX_QUEUE_SIZE:
            self.queue.pop(0)
        full = f"{username}: {message}"
        if len(full) <= MAX_CHARS:
            self.queue.append(DisplayItem(full))
        else:
            for block in split_text(username, message):
                self.queue.append(DisplayItem(block))

    @staticmethod
    def _render(items: list[DisplayItem]) -> str:
        return "\n---\n".join(i.text for i in items)

    def _fits(self, item: DisplayItem) -> bool:
        return len(self._render(self.active + [item])) <= MAX_CHARS

    @property
    def current(self) -> str:
        return self._render(self.active)

    def _try_advance(self) -> bool:
        if self.queue and self._fits(self.queue[0]):
            item = self.queue.pop(0)
            item.mark_shown()
            self.active.append(item)
            return True
        if self.queue and self.active and self.active[0].can_be_removed:
            self.active.pop(0)
            return True
        return False

    def update(self) -> str | None:
        for item in self.active:
            item.mark_shown()
        while self._try_advance():
            pass


manager = DisplayManager()


async def display_loop() -> None:
    last_sent_time: float = 0.0

    while True:
        manager.update()

        now = time.monotonic()

        if now - last_sent_time >= T_OSC_RATE_LIMIT:
            current = manager.current
            send_chatbox(current)
            last_sent_time = now
            if current:
                print(f"[ChatBox]\n{current}\n{'-'*40}")
            else:
                print("[ChatBox] <cleared>\n" + "-"*40)

        await asyncio.sleep(T_REFRESH)
