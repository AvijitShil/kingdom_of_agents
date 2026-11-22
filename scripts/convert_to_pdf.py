"""
Converts Markdown Literature Survey to a beautifully styled PDF via Chrome Headless.
"""

import os
import subprocess
import markdown

DOCS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs"))
MD_PATH = os.path.join(DOCS_DIR, "literature_survey.md")
HTML_PATH = os.path.join(DOCS_DIR, "literature_survey.html")
PDF_PATH = os.path.join(DOCS_DIR, "literature_survey.pdf")


def convert():
    print(f"Reading markdown from: {MD_PATH}")
    with open(MD_PATH, "r", encoding="utf-8") as f:
        md_content = f.read()

    html_body = markdown.markdown(md_content, extensions=["tables", "fenced_code"])

    html_template = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>EON Kingdom of Agents: Literature Survey</title>
<style>
    @page {
        size: A4;
        margin: 18mm 15mm 18mm 15mm;
    }
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        font-size: 10pt;
        line-height: 1.55;
        color: #24292f;
        background-color: #ffffff;
        margin: 0;
        padding: 0;
    }
    h1 {
        font-size: 18pt;
        border-bottom: 2px solid #0969da;
        padding-bottom: 8px;
        color: #1f2328;
        margin-top: 0;
    }
    h2 {
        font-size: 13pt;
        border-bottom: 1px solid #d0d7de;
        padding-bottom: 5px;
        margin-top: 22px;
        color: #0969da;
        page-break-after: avoid;
    }
    h3 {
        font-size: 11pt;
        margin-top: 16px;
        color: #1f2328;
        page-break-after: avoid;
    }
    p, li {
        text-align: justify;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 14px 0;
        font-size: 8.5pt;
        page-break-inside: avoid;
    }
    th, td {
        border: 1px solid #d0d7de;
        padding: 6px 8px;
        text-align: left;
    }
    th {
        background-color: #f6f8fa;
        font-weight: 600;
        color: #24292f;
    }
    tr:nth-child(even) {
        background-color: #fafbfc;
    }
    code {
        font-family: Consolas, "Courier New", monospace;
        background-color: #f6f8fa;
        padding: 1px 4px;
        border-radius: 3px;
        font-size: 9pt;
    }
    pre {
        background-color: #f6f8fa;
        border: 1px solid #d0d7de;
        border-radius: 6px;
        padding: 10px;
        overflow-x: auto;
        font-size: 8.5pt;
        line-height: 1.4;
        page-break-inside: avoid;
    }
    pre code {
        background-color: transparent;
        padding: 0;
    }
    blockquote {
        margin: 12px 0;
        padding: 6px 14px;
        color: #2b3a67;
        background-color: #f0f7ff;
        border-left: 4px solid #0969da;
        border-radius: 0 4px 4px 0;
    }
    ul, ol {
        padding-left: 20px;
    }
    hr {
        border: 0;
        height: 1px;
        background-color: #d0d7de;
        margin: 18px 0;
    }
</style>
</head>
<body>
""" + html_body + """
</body>
</html>"""

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"Generated HTML at: {HTML_PATH}")

    chrome_candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    ]
    browser_exe = None
    for cand in chrome_candidates:
        if os.path.exists(cand):
            browser_exe = cand
            break

    if not browser_exe:
        raise RuntimeError("Neither Chrome nor Edge was found.")

    print(f"Using browser: {browser_exe}")
    html_url = "file:///" + HTML_PATH.replace(os.sep, "/")
    cmd = [
        browser_exe,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={PDF_PATH}",
        html_url
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(PDF_PATH):
        size_kb = os.path.getsize(PDF_PATH) / 1024
        print(f"[+] Successfully generated PDF: {PDF_PATH} ({size_kb:.1f} KB)")
    else:
        print(f"[-] PDF conversion failed: {res.stderr}")


if __name__ == "__main__":
    convert()
