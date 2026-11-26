"""The /docs page, with a dark mode switch added."""

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse

# swagger ui ships dark styles under html.dark-mode, but only its standalone layout has a
# switch for them and fastapi does not load that layout
DARK_MODE = """
<style>
html { background: #fff; }
#theme-toggle {
  position: fixed; top: 12px; right: 16px; z-index: 10; padding: 6px 12px;
  border: 1px solid #888; border-radius: 4px; background: #fff; color: #3b4151;
  font: 14px sans-serif; cursor: pointer;
}
html.dark-mode #theme-toggle { background: #1c2022; color: #e4e6e6; }
</style>
<script>
const root = document.documentElement
const saved = localStorage.getItem("theme")
const dark = saved ? saved === "dark" : matchMedia("(prefers-color-scheme: dark)").matches
root.classList.toggle("dark-mode", dark)

addEventListener("DOMContentLoaded", () => {
  const button = document.createElement("button")
  button.id = "theme-toggle"
  const label = () => {
    button.textContent = root.classList.contains("dark-mode") ? "Light mode" : "Dark mode"
  }
  button.onclick = () => {
    localStorage.setItem("theme", root.classList.toggle("dark-mode") ? "dark" : "light")
    label()
  }
  label()
  document.body.append(button)
})
</script>
"""


def add_docs_page(app: FastAPI) -> None:
    @app.get("/docs", include_in_schema=False)
    def docs() -> HTMLResponse:
        page = get_swagger_ui_html(openapi_url=app.openapi_url, title=f"{app.title} - Swagger UI")
        return HTMLResponse(page.body.decode().replace("</head>", DARK_MODE + "</head>"))
