import asyncio
import logging
from urllib.parse import urlparse

import httpx
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# =========================
# CONFIG
# =========================
BOT_TOKEN = "YOUR_BOT_TOKEN"

# Các domain chỉ là ví dụ để nhận diện.
# Bot KHÔNG bypass CAPTCHA/quảng cáo/nhiệm vụ.
SUPPORTED_DOMAINS = {
    "link4m.com",
    "yeumoney.com",
    "topslink.io",
    "layma.net",
}

MAX_REDIRECTS = 15
REQUEST_TIMEOUT = 15.0

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def normalize_url(text: str) -> str | None:
    text = text.strip()
    if not text:
        return None

    if not text.startswith(("http://", "https://")):
        text = "https://" + text

    parsed = urlparse(text)
    if not parsed.netloc:
        return None

    return text


def get_domain(url: str) -> str:
    hostname = (urlparse(url).hostname or "").lower()
    return hostname.removeprefix("www.")


def supported_domain(url: str) -> bool:
    domain = get_domain(url)
    return any(
        domain == item or domain.endswith("." + item)
        for item in SUPPORTED_DOMAINS
    )


async def resolve_public_redirects(url: str) -> tuple[str, list[str]]:
    """
    Chỉ theo redirect HTTP công khai.
    Không giải/bypass CAPTCHA, anti-bot, login hoặc nhiệm vụ.
    """
    history = []

    timeout = httpx.Timeout(REQUEST_TIMEOUT)

    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=True,
        max_redirects=MAX_REDIRECTS,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (compatible; TelegramLinkBot/1.0)"
            )
        },
    ) as client:
        response = await client.get(url)

        for item in response.history:
            history.append(str(item.url))

        history.append(str(response.url))

        return str(response.url), history


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Gửi cho tôi một link.\n\n"
        "Bot sẽ tự theo các redirect HTTP công khai và trả URL cuối cùng.\n"
        "Nếu trang yêu cầu CAPTCHA hoặc thao tác người dùng, bạn cần tự hoàn thành bước đó."
    )


async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    url = normalize_url(update.message.text)

    if not url:
        await update.message.reply_text("❌ Link không hợp lệ.")
        return

    domain = get_domain(url)

    if not supported_domain(url):
        await update.message.reply_text(
            f"⚠️ Domain `{domain}` chưa nằm trong danh sách hỗ trợ.\n"
            "Bot vẫn có thể thử xử lý redirect HTTP công khai.",
            parse_mode="Markdown",
        )

    message = await update.message.reply_text("⏳ Đang kiểm tra redirect...")

    try:
        final_url, history = await resolve_public_redirects(url)

        if len(history) > 1:
            chain = "\n".join(
                f"{i + 1}. {item}"
                for i, item in enumerate(history[-10:])
            )
        else:
            chain = "(Không có redirect HTTP công khai.)"

        await message.edit_text(
            "✅ Hoàn tất xử lý redirect công khai.\n\n"
            f"🔗 Link cuối:\n{final_url}\n\n"
            f"📍 Chuỗi redirect:\n{chain}\n\n"
            "Nếu trang cuối yêu cầu CAPTCHA/đăng nhập/nhiệm vụ, "
            "hãy tự hoàn thành trên trang đó."
        )

    except httpx.TooManyRedirects:
        await message.edit_text(
            "❌ Link có quá nhiều redirect hoặc vòng lặp redirect."
        )
    except httpx.TimeoutException:
        await message.edit_text(
            "⏱️ Máy chủ phản hồi quá lâu. Vui lòng thử lại."
        )
    except httpx.HTTPError as exc:
        logger.warning("HTTP error: %s", exc)
        await message.edit_text(
            "❌ Không thể truy cập link bằng HTTP client."
        )
    except Exception:
        logger.exception("Unexpected error")
        await message.edit_text(
            "❌ Đã xảy ra lỗi không xác định."
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception(
        "Telegram error",
        exc_info=context.error,
    )


def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN":
        raise RuntimeError(
            "Hãy thay YOUR_BOT_TOKEN bằng token bot Telegram của bạn."
        )

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link)
    )
    app.add_error_handler(error_handler)

    logger.info("Bot đang chạy...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
