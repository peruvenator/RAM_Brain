"""Inject blog data into the HTML template."""
import json

# Read slim data
with open("blog-data-slim.json", "r", encoding="utf-8") as f:
    data = f.read()

# Read HTML template
with open("blog-landing-page.html", "r", encoding="utf-8") as f:
    html = f.read()

# Replace placeholder with actual data
html = html.replace("BLOG_DATA_PLACEHOLDER", data)

# Write final HTML
with open("blog-landing-page.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"Injected {len(data)} bytes of blog data into HTML")
print(f"Final HTML size: {len(html)} bytes ({len(html)//1024}KB)")
