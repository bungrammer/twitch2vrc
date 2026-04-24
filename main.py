import asyncio

from config import load_config
from osc import init_osc, send_chatbox, display_loop
from platforms.twitch import TwitchBot


async def main() -> None:
    config = load_config()

    init_osc(config.vrc_osc_host, config.vrc_osc_port)
    print(f"Sending OSC to {config.vrc_osc_host}:{config.vrc_osc_port}")
    print("-" * 40)

    bot = TwitchBot(config)
    try:
        await asyncio.gather(
            bot.start(),
            display_loop()
        )
    finally:
        send_chatbox("")
        print("\n[ChatBox] Cleared on exit.")


if __name__ == "__main__":
    asyncio.run(main())
