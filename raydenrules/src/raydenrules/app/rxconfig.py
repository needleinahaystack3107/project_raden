import reflex as rx

config = rx.Config(
    app_name="reflex_app",
    db_url="sqlite:///reflex.db",
    disable_plugins=["reflex.plugins.sitemap.SitemapPlugin"],
    # backend_port defaults to 8000 - Reflex handles its own backend
)
