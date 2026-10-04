import os
import re
from urllib.parse import urlparse

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


# =========================================================
# CẤU HÌNH
# =========================================================

BOT_TOKEN = os.environ["8984311646:AAGxSxN6yiD2TXKv9M0gogQEebH9oQVa7D8"]

SUPPORTED_DOMAINS = {
    "link4m.com",
    "yeumoney.com",
    "topslink.io",
    "layma.net",
}

MAX_WAIT = 45


# =========================================================
# KIỂM TRA URL
# =========================================================

def normalize_url(text: str):
    text = text.strip()

    if not text:
        return None

    if not re.match(r"^https?://", text, re.IGNORECASE):
        text = "https://" + text

    try:
        host = (urlparse(text).hostname or "").lower()

        for domain in SUPPORTED_DOMAINS:
            if host == domain or host.endswith("." + domain):
                return text

    except Exception:
        pass

    return None


# =========================================================
# MENU
# =========================================================

def main_menu():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔗 Vượt link",
                callback_data="resolve"
            ),
            InlineKeyboardButton(
                "📖 Hướng dẫn",
                callback_data="help"
            ),
        ],
        [
            InlineKeyboardButton(
                "🌐 Domain hỗ trợ",
                callback_data="domains"
            ),
            InlineKeyboardButton(
                "⚙️ Cài đặt",
                callback_data="settings"
            ),
        ],
        [
            InlineKeyboardButton(
                "ℹ️ Trạng thái",
                callback_data="status"
            ),
        ],
    ])


def result_menu():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔄 Thử lại",
                callback_data="retry"
            ),
            InlineKeyboardButton(
                "🔗 Link mới",
                callback_data="resolve"
            ),
        ],
        [
            InlineKeyboardButton(
                "🏠 Menu chính",
                callback_data="home"
            ),
        ],
    ])


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🤖 *LINK BOT*\n\n"
        "Chào bạn! 👋\n\n"
        "Gửi link cần xử lý hoặc chọn một chức năng bên dưới.\n\n"
        "🌐 Playwright Browser\n"
        "⚡ Async processing\n"
        "🔄 Theo dõi chuyển hướng công khai\n\n"
        "⚠️ CAPTCHA/anti-bot không được tự động vượt.",
        parse_mode="Markdown",
        reply_markup=main_menu(),
    )


# =========================================================
# HELP
# =========================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "📖 *HƯỚNG DẪN*\n\n"
        "① Bấm 🔗 Vượt link.\n"
        "② Gửi URL.\n"
        "③ Bot mở URL bằng trình duyệt.\n"
        "④ Bot chờ chuyển hướng công khai.\n"
        "⑤ Bot trả URL hiện tại.\n\n"
        "Bạn cũng có thể gửi URL trực tiếp mà không cần "
        "bấm nút.\n\n"
        "⚠️ Nếu website yêu cầu CAPTCHA/anti-bot, "
        "bot sẽ dừng.",
        parse_mode="Markdown",
        reply_markup=main_menu(),
    )


# =========================================================
# DOMAIN
# =========================================================

async def show_domains(message):

    domains = "\n".join(
        f"• `{domain}`"
        for domain in sorted(SUPPORTED_DOMAINS)
    )

    await message.reply_text(
        "🌐 *DOMAIN ĐƯỢC HỖ TRỢ*\n\n"
        f"{domains}\n\n"
        "Các domain khác sẽ không được xử lý.",
        parse_mode="Markdown",
        reply_markup=main_menu(),
    )


# =========================================================
# SETTINGS
# =========================================================

async def show_settings(message):

    await message.reply_text(
        "⚙️ *CÀI ĐẶT BOT*\n\n"
        "🌐 Browser: 🟢 Playwright\n"
        "🔄 Theo dõi chuyển hướng: 🟢 Bật\n"
        f"⏱ Thời gian chờ: `{MAX_WAIT}` giây\n"
        "🔐 CAPTCHA bypass: 🔴 Tắt",
        parse_mode="Markdown",
        reply_markup=main_menu(),
    )


# =========================================================
# STATUS
# =========================================================

async def show_status(message):

    await message.reply_text(
        "ℹ️ *TRẠNG THÁI BOT*\n\n"
        "🟢 Bot: Online\n"
        "🌐 Playwright: Enabled\n"
        "⚡ Async: Enabled\n"
        "🔄 Redirect tracking: Enabled\n"
        "🔐 CAPTCHA bypass: Disabled",
        parse_mode="Markdown",
        reply_markup=main_menu(),
    )


# =========================================================
# PLAYWRIGHT
# =========================================================

async def process_link(
    url: str,
    status_message
):

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        page = await browser.new_page()

        try:

            await status_message.edit_text(
                "🌐 *Đang mở link...*\n\n"
                "⏳ Đang tải trang...",
                parse_mode="Markdown",
            )

            await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            await page.wait_for_timeout(5000)

            # -------------------------------------------------
            # PHÁT HIỆN CAPTCHA
            # -------------------------------------------------

            captcha = await page.locator(
                "iframe[src*='captcha'],"
                "iframe[src*='recaptcha'],"
                "iframe[src*='hcaptcha'],"
                "[class*='captcha'],"
                "[id*='captcha']"
            ).count()

            if captcha:

                await status_message.edit_text(
                    "🧩 *Phát hiện CAPTCHA / anti-bot*\n\n"
                    "Bot không tự động vượt cơ chế bảo vệ này.\n\n"
                    "Bạn có thể xử lý CAPTCHA thủ công rồi "
                    "gửi lại link.",
                    parse_mode="Markdown",
                    reply_markup=result_menu(),
                )

                return

            # -------------------------------------------------
            # THEO DÕI URL
            # -------------------------------------------------

            last_url = page.url
            stable_count = 0

            for _ in range(MAX_WAIT // 2):

                await page.wait_for_timeout(2000)

                current_url = page.url

                if current_url == last_url:

                    stable_count += 1

                    if stable_count >= 2:
                        break

                else:

                    last_url = current_url
                    stable_count = 0

            final_url = page.url

            # -------------------------------------------------
            # KẾT QUẢ
            # -------------------------------------------------

            await status_message.edit_text(
                "✅ *ĐÃ XỬ LÝ XONG*\n\n"
                f"🔗 `{final_url}`",
                parse_mode="Markdown",
                reply_markup=result_menu(),
            )

        except PlaywrightTimeoutError:

            await status_message.edit_text(
                "⏱️ *HẾT THỜI GIAN CHỜ*\n\n"
                "Website phản hồi quá lâu.\n"
                "Hãy thử lại.",
                parse_mode="Markdown",
                reply_markup=result_menu(),
            )

        except Exception as error:

            await status_message.edit_text(
                "❌ *KHÔNG XỬ LÝ ĐƯỢC*\n\n"
                f"Lỗi: `{type(error).__name__}`",
                parse_mode="Markdown",
                reply_markup=result_menu(),
            )

        finally:

            await browser.close()


# =========================================================
# NHẬN LINK
# =========================================================

async def handle_link(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text or ""

    url = normalize_url(text)

    if not url:

        await update.message.reply_text(
            "❌ *LINK KHÔNG ĐƯỢC HỖ TRỢ*\n\n"
            "Bot hiện hỗ trợ:\n\n"
            "• link4m.com\n"
            "• yeumoney.com\n"
            "• topslink.io\n"
            "• layma.net",
            parse_mode="Markdown",
            reply_markup=main_menu(),
        )

        return

    # Lưu link để nút Thử lại sử dụng
    context.user_data["last_url"] = url

    status = await update.message.reply_text(
        "⏳ Chuẩn bị xử lý..."
    )

    await process_link(
        url,
        status
    )


# =========================================================
# NÚT INLINE
# =========================================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    action = query.data

    # -----------------------------------------------------
    # HOME
    # -----------------------------------------------------

    if action == "home":

        await query.message.reply_text(
            "🏠 *MENU CHÍNH*\n\n"
            "Chọn chức năng:",
            parse_mode="Markdown",
            reply_markup=main_menu(),
        )

    # -----------------------------------------------------
    # RESOLVE
    # -----------------------------------------------------

    elif action == "resolve":

        await query.message.reply_text(
            "🔗 *VƯỢT LINK*\n\n"
            "Hãy gửi URL cần xử lý.",
            parse_mode="Markdown",
            reply_markup=main_menu(),
        )

    # -----------------------------------------------------
    # RETRY
    # -----------------------------------------------------

    elif action == "retry":

        url = context.user_data.get("last_url")

        if not url:

            await query.message.reply_text(
                "⚠️ Chưa có link trước đó.",
                reply_markup=main_menu(),
            )

            return

        status = await query.message.reply_text(
            "🔄 Đang thử lại..."
        )

        await process_link(
            url,
            status
        )

    # -----------------------------------------------------
    # HELP
    # -----------------------------------------------------

    elif action == "help":

        await query.message.reply_text(
            "📖 *HƯỚNG DẪN*\n\n"
            "Gửi link trực tiếp cho bot hoặc bấm "
            "🔗 Vượt link.\n\n"
            "Bot sẽ mở trang bằng Playwright và theo "
            "dõi chuyển hướng công khai.\n\n"
            "⚠️ CAPTCHA/anti-bot không được tự động vượt.",
            parse_mode="Markdown",
            reply_markup=main_menu(),
        )

    # -----------------------------------------------------
    # DOMAINS
    # -----------------------------------------------------

    elif action == "domains":

        await show_domains(
            query.message
        )

    # -----------------------------------------------------
    # SETTINGS
    # -----------------------------------------------------

    elif action == "settings":

        await show_settings(
            query.message
        )

    # -----------------------------------------------------
    # STATUS
    # -----------------------------------------------------

    elif action == "status":

        await show_status(
            query.message
        )


# =========================================================
# MAIN
# =========================================================

def main():

    if not BOT_TOKEN:

        raise RuntimeError(
            "Không tìm thấy BOT_TOKEN."
        )

    application = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    application.add_handler(
        CommandHandler(
            "help",
            help_command
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_link
        )
    )

    print("🤖 Bot đang chạy...")

    application.run_polling()


if __name__ == "__main__":
    main()
