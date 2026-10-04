import os
import asyncio
import logging
from urllib.parse import urlparse

from aiohttp import web
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# =========================
# CONFIG
# =========================

BOT_TOKEN = os.getenv("8984311646:AAGxSxN6yiD2TXKv9M0gogQEebH9oQVa7D8")
PORT = int(os.getenv("PORT", "10000"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN chưa được cài trong Environment Variables.")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# Các domain bot nhận diện
SUPPORTED_DOMAINS = {
    "link4m.com",
    "www.link4m.com",
    "yeumoney.com",
    "www.yeumoney.com",
    "topslink.io",
    "www.topslink.io",
    "layma.net",
    "www.layma.net",
}


# =========================
# KEYBOARD
# =========================

def main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔗 Vượt link", callback_data="new"),
            InlineKeyboardButton("🌐 Domain", callback_data="domains"),
        ],
        [
            InlineKeyboardButton("📖 Hướng dẫn", callback_data="help"),
            InlineKeyboardButton("ℹ️ Trạng thái", callback_data="status"),
        ],
    ])


# =========================
# URL
# =========================

def valid_url(url):
    try:
        parsed = urlparse(url)

        return (
            parsed.scheme in ("http", "https")
            and bool(parsed.netloc)
        )

    except Exception:
        return False


def get_domain(url):
    try:
        return urlparse(url).netloc.lower().split(":")[0]
    except Exception:
        return ""


def is_supported(url):
    return get_domain(url) in SUPPORTED_DOMAINS


# =========================
# TELEGRAM COMMANDS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = (
        "🤖 *BOT VƯỢT LINK*\n\n"
        "Gửi link rút gọn cho bot.\n\n"
        "Bot sẽ mở trang bằng Chromium và theo dõi "
        "điều hướng bình thường của trang.\n\n"
        "⚠️ Nếu xuất hiện CAPTCHA, bạn phải tự hoàn thành. "
        "Bot không tự giải hoặc bypass CAPTCHA."
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=main_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = (
        "📖 *HƯỚNG DẪN*\n\n"
        "1️⃣ Gửi URL cho bot.\n"
        "2️⃣ Bot mở URL bằng Chromium.\n"
        "3️⃣ Bot chờ trang xử lý/điều hướng.\n"
        "4️⃣ Nếu có CAPTCHA, người dùng tự xử lý.\n"
        "5️⃣ Bot trả URL hiện tại sau khi trang điều hướng.\n\n"
        "Bot không bypass CAPTCHA hoặc các cơ chế bảo vệ."
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=main_keyboard(),
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🟢 Bot đang hoạt động.\n"
        "🌐 Chromium: OK\n"
        "🤖 Telegram: OK\n"
        "🔐 CAPTCHA: người dùng tự xử lý.",
        reply_markup=main_keyboard(),
    )


async def domains_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🌐 *DOMAIN ĐANG HỖ TRỢ*\n\n"
        "• link4m.com\n"
        "• yeumoney.com\n"
        "• topslink.io\n"
        "• layma.net",
        parse_mode="Markdown",
        reply_markup=main_keyboard(),
    )


# =========================
# PLAYWRIGHT
# =========================

async def process_link(url):

    async with async_playwright() as playwright:

        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )

        page = await browser.new_page(
            viewport={
                "width": 1280,
                "height": 900,
            }
        )

        try:

            await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30000,
            )

            # Cho JavaScript/redirect có thời gian chạy
            await page.wait_for_timeout(5000)

            # =========================
            # CAPTCHA DETECTION
            # =========================

            captcha_selectors = [
                "iframe[src*='recaptcha']",
                "iframe[src*='hcaptcha']",
                ".g-recaptcha",
                ".h-captcha",
                "[data-sitekey]",
            ]

            for selector in captcha_selectors:

                try:

                    element = page.locator(selector).first

                    if await element.is_visible(timeout=500):

                        return {
                            "status": "captcha",
                            "url": page.url,
                        }

                except Exception:
                    pass

            # =========================
            # WAIT REDIRECT
            # =========================

            old_url = page.url

            for _ in range(15):

                await page.wait_for_timeout(1000)

                if page.url != old_url:

                    old_url = page.url

            return {
                "status": "success",
                "url": page.url,
            }

        except PlaywrightTimeoutError:

            return {
                "status": "timeout",
                "url": page.url,
            }

        except Exception as error:

            return {
                "status": "error",
                "url": page.url,
                "message": str(error),
            }

        finally:

            await browser.close()


# =========================
# RECEIVE LINK
# =========================

async def receive_link(update: Update, context: ContextTypes.DEFAULT_TYPE):

    url = update.message.text.strip()

    if not valid_url(url):

        await update.message.reply_text(
            "❌ Link không hợp lệ.\n\n"
            "Ví dụ:\n"
            "https://example.com/abc",
            reply_markup=main_keyboard(),
        )

        return

    domain = get_domain(url)

    if not is_supported(url):

        await update.message.reply_text(
            f"⚠️ Domain `{domain}` chưa nằm trong danh sách hỗ trợ.\n\n"
            "Bot vẫn sẽ thử mở trang.",
            parse_mode="Markdown",
        )

    message = await update.message.reply_text(
        "⏳ Đang mở link...\n\n"
        "🌐 Chromium đang xử lý..."
    )

    try:

        result = await process_link(url)

        # CAPTCHA
        if result["status"] == "captcha":

            await message.edit_text(
                "🧩 *Phát hiện CAPTCHA*\n\n"
                "Bot đã dừng tại đây.\n"
                "Bạn cần tự hoàn thành CAPTCHA.",
                parse_mode="Markdown",
            )

            return

        # SUCCESS
        if result["status"] == "success":

            final_url = result["url"]

            await message.edit_text(
                "✅ *Đã xử lý xong*\n\n"
                f"🔗 `{final_url}`",
                parse_mode="Markdown",
            )

            return

        # TIMEOUT
        if result["status"] == "timeout":

            await message.edit_text(
                "⏱️ Trang phản hồi quá lâu.\n\n"
                f"URL hiện tại:\n{result['url']}"
            )

            return

        # ERROR
        await message.edit_text(
            "❌ Có lỗi khi mở trang.\n\n"
            f"{result.get('message', 'Unknown error')}"
        )

    except Exception as error:

        logging.exception("BOT ERROR")

        await message.edit_text(
            "❌ Bot gặp lỗi:\n\n"
            f"{type(error).__name__}: {error}"
        )


# =========================
# BUTTONS
# =========================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    action = query.data

    if action == "new":

        await query.message.reply_text(
            "🔗 Gửi link rút gọn cần xử lý.",
            reply_markup=main_keyboard(),
        )

    elif action == "domains":

        await query.message.reply_text(
            "🌐 Domain:\n\n"
            "• link4m.com\n"
            "• yeumoney.com\n"
            "• topslink.io\n"
            "• layma.net",
            reply_markup=main_keyboard(),
        )

    elif action == "help":

        await query.message.reply_text(
            "📖 Gửi URL → Chromium mở trang → "
            "nếu có CAPTCHA thì bạn tự xử lý → "
            "bot theo dõi điều hướng.",
            reply_markup=main_keyboard(),
        )

    elif action == "status":

        await query.message.reply_text(
            "🟢 Bot đang chạy.",
            reply_markup=main_keyboard(),
        )


# =========================
# RENDER HEALTH CHECK
# =========================

async def health(request):

    return web.Response(
        text="BOT ONLINE",
        status=200,
    )


async def start_web_server():

    app = web.Application()

    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    runner = web.AppRunner(app)

    await runner.setup()

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        PORT,
    )

    await site.start()

    logging.info(
        f"Health server running on port {PORT}"
    )

    return runner


# =========================
# BOT
# =========================

async def start_bot():

    application = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("help", help_command)
    )

    application.add_handler(
        CommandHandler("status", status_command)
    )

    application.add_handler(
        CommandHandler("domains", domains_command)
    )

    application.add_handler(
        CallbackQueryHandler(button_handler)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_link,
        )
    )

    await application.initialize()

    await application.start()

    await application.updater.start_polling(
        drop_pending_updates=True
    )

    logging.info("Telegram bot started.")

    return application


# =========================
# MAIN
# =========================

async def main():

    web_runner = await start_web_server()

    bot = await start_bot()

    try:

        await asyncio.Event().wait()

    finally:

        await bot.updater.stop()

        await bot.stop()

        await bot.shutdown()

        await web_runner.cleanup()


if __name__ == "__main__":

    asyncio.run(main())
