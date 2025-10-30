import reflex as rx

config = rx.Config(
    app_name="reflex_app",
    db_url="sqlite:///reflex.db",
    disable_plugins=["reflex.plugins.sitemap.SitemapPlugin"],
)
