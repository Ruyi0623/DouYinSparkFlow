import os, sys
import subprocess
import traceback
from playwright.sync_api import sync_playwright
from utils.config import DEBUG, get_environment, Environment

PLAYWRIGHT_BROWSERS_PATH = "../chrome"


def install_browser():
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
        print("浏览器安装完成，请重新运行程序。")
    except subprocess.CalledProcessError as e:
        print(f"发生未知错误：{e}")


def find_chromium_executable():
    candidates = [
        "chromium-browser",
        "chromium",
        "google-chrome",
        "google-chrome-stable",
    ]
    for name in candidates:
        result = subprocess.run(["which", name], capture_output=True, text=True)
        path = result.stdout.strip()
        if path:
            return path
    return None


def has_display():
    """检测是否有可用的显示器"""
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def get_browser():
    headless = True

    env = get_environment()
    if env == Environment.LOCAL:
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.abspath(
            os.path.join(os.path.dirname(__file__), PLAYWRIGHT_BROWSERS_PATH)
        )
        # 只有本地 + DEBUG + 有显示器，才启用有头模式
        if DEBUG and has_display():
            headless = False
        elif DEBUG and not has_display():
            print("警告：检测到无显示器环境，强制使用 headless 模式")
    elif env == Environment.PACKED:
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.abspath(
            os.path.join(os.path.dirname(sys.executable), PLAYWRIGHT_BROWSERS_PATH)
        )

    try:
        playwright = sync_playwright().start()
        chromium_path = find_chromium_executable()

        if chromium_path:
            print(f"使用系统 Chromium：{chromium_path}")
            browser = playwright.chromium.launch(
                executable_path=chromium_path,
                headless=headless,
            )
        else:
            print("未找到系统 Chromium，回退到 Playwright 自带版本")
            browser = playwright.chromium.launch(headless=headless)

        return playwright, browser

    except Exception as e:
        if "Executable doesn't exist" in str(e) and env != Environment.GITHUBACTION:
            print("浏览器可执行文件不存在！")
            install_browser()
            sys.exit(1)
        else:
            traceback.print_exc()
            sys.exit(1)  # 修复：异常时主动退出，避免返回 None 导致解包报错
