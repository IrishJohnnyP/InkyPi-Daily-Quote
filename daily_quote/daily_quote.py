from plugins.base_plugin.base_plugin import BasePlugin
from utils.http_client import get_http_session
import logging
import random

# FIX: name is required; 'name' causes a crash
logger = logging.getLogger(__name__)

# NOTE:
# This constant name is intentionally kept the same
# so this file is a TRUE drop-in replacement.
ZENQUOTES_URL = "https://quote.butternut.cloud"

FALLBACK_QUOTES = [
    {"q": "The only way to do great work is to love what you do.", "a": "Steve Jobs"},
    {"q": "In the middle of difficulty lies opportunity.", "a": "Albert Einstein"},
    {"q": "Simplicity is the ultimate sophistication.", "a": "Leonardo da Vinci"},
    {"q": "The best time to plant a tree was 20 years ago. The second best time is now.", "a": "Chinese Proverb"},
    {"q": "Be yourself; everyone else is already taken.", "a": "Oscar Wilde"},
    {"q": "Do what you can, with what you have, where you are.", "a": "Theodore Roosevelt"},
    {"q": "It does not matter how slowly you go as long as you do not stop.", "a": "Confucius"},
    {"q": "Life is what happens when you're busy making other plans.", "a": "John Lennon"},
    {"q": "The unexamined life is not worth living.", "a": "Socrates"},
    {"q": "To be or not to be, that is the question.", "a": "William Shakespeare"},
    {"q": "I think, therefore I am.", "a": "Rene Descartes"},
    {"q": "That which does not kill us makes us stronger.", "a": "Friedrich Nietzsche"},
    {"q": "Not all those who wander are lost.", "a": "J.R.R. Tolkien"},
    {"q": "The journey of a thousand miles begins with a single step.", "a": "Lao Tzu"},
    {"q": "Stay hungry, stay foolish.", "a": "Steve Jobs"},
]


class DailyQuote(BasePlugin):

    def generate_settings_template(self):
        template_params = super().generate_settings_template()
        template_params["style_settings"] = True
        return template_params

    def generate_image(self, settings, device_config):
        dimensions = device_config.get_resolution()
        if device_config.get_config("orientation") == "vertical":
            dimensions = dimensions[::-1]

        font_size = settings.get("font_size", "normal")

        # --- SECURITY FIX ---
        # Retrieve the key from InkyPi's environment
        app_key = device_config.load_env_key("app_key")
        # --------------------

        quote_data = self._fetch_quote(app_key)

        template_params = {
            "quote": quote_data["q"],
            "author": quote_data["a"],
            "font_size": font_size,
            "plugin_settings": settings,
        }

        image = self.render_image(
            dimensions, "daily_quote.html", "daily_quote.css", template_params
        )
        return image

    def _get_auth_headers(self, app_key):
        """Builds the custom headers needed to pass the Cloudflare Worker security check."""
        if not app_key:
            logger.error("Security Error: app_key was not found by device_config.")
            return {}
        return {"X-App-Key": app_key}

    def _fetch_quote(self, app_key):
        session = get_http_session()
        headers = self._get_auth_headers(app_key)
        
        try:
            # Call the Cloudflare Worker instead of ZenQuotes directly, 
            # now passing the X-App-Key header
            resp = session.get(ZENQUOTES_URL, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            # Worker returns:
            # { "text": "...", "author": "...", "source": "..." }
            # Convert it back to the original ZenQuotes shape
            if isinstance(data, dict) and "text" in data:
                return {
                    "q": data.get("text", ""),
                    "a": data.get("author", "Unknown"),
                }

        except Exception as e:
            logger.error("Quote fetch failed: %s", e)

        return random.choice(FALLBACK_QUOTES)
