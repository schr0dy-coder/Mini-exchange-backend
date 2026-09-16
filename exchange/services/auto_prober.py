import os
import sys
import time
import logging
import urllib.request
from threading import Thread

logger = logging.getLogger(__name__)

# Render free-tier spins down after 15 minutes of inactivity.
# We probe every 10 minutes (600s) to keep it warm.
DEFAULT_PROBE_INTERVAL = 600
PROBE_INTERVAL = int(os.getenv("AUTO_PROBE_INTERVAL", DEFAULT_PROBE_INTERVAL))
PROBE_ENABLED = os.getenv("ENABLE_AUTO_PROBE", "True").lower() in ("true", "1", "yes")


def get_probe_url():
    """
    Determine the public URL to probe.
    1. AUTO_PROBE_URL if explicitly provided in environment.
    2. RENDER_EXTERNAL_URL (automatically populated by Render).
    3. Production fallback URL if running on Render or not in debug mode.
    """
    custom_url = os.getenv("AUTO_PROBE_URL")
    if custom_url:
        return custom_url

    render_url = os.getenv("RENDER_EXTERNAL_URL")
    if render_url:
        return f"{render_url.rstrip('/')}/api/health/"

    # If running on Render (RENDER environment variable is present)
    if os.getenv("RENDER") == "true":
        return "https://mini-exchange-backend.onrender.com/api/health/"

    # If debug is explicitly disabled, assume production
    if os.getenv("DEBUG", "True").lower() in ("false", "0", "no"):
        return "https://mini-exchange-backend.onrender.com/api/health/"

    return None


def probe_loop():
    url = get_probe_url()
    if not url:
        logger.info("[AutoProber] Local development detected without target URL. Skipping auto-probing.")
        return

    logger.info(f"[AutoProber] Initialized. Will ping {url} every {PROBE_INTERVAL}s to keep Render active.")

    # Allow server to complete boot sequence before sending first ping
    time.sleep(20)

    while True:
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "MiniExchange-AutoProber/1.0"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    logger.info(f"[AutoProber] Keep-alive ping successful (status 200)")
                else:
                    logger.warning(f"[AutoProber] Keep-alive ping returned status {resp.status}")
        except Exception as err:
            logger.warning(f"[AutoProber] Keep-alive ping failed: {err}")

        time.sleep(PROBE_INTERVAL)


def start_auto_prober():
    """Start the background auto-probing daemon thread."""
    if not PROBE_ENABLED:
        logger.info("[AutoProber] Auto-probing is disabled via ENABLE_AUTO_PROBE.")
        return

    # Do not run during management commands
    management_commands = {"migrate", "makemigrations", "collectstatic", "test", "createsuperuser", "shell"}
    if any(cmd in sys.argv for cmd in management_commands):
        return

    # In local runserver, prevent starting duplicate threads in the reloader parent process
    if "runserver" in sys.argv and os.environ.get("RUN_MAIN") != "true":
        return

    thread = Thread(target=probe_loop, name="AutoProberThread", daemon=True)
    thread.start()
