from pathlib import Path

files = [
    Path('catalog/templates/catalog/home.html'),
    Path('templates/catalog/includes/navbar.html'),
]

for p in files:
    text = p.read_text(encoding='utf-8')
    lines = [line.rstrip() for line in text.splitlines()]
    p.write_text('\n'.join(lines) + '\n', encoding='utf-8')
