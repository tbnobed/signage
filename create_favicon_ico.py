#!/usr/bin/env python3
"""Create favicon.ico from PNG icons."""

from PIL import Image

# Open the 32x32 PNG
img32 = Image.open('static/icons/favicon-32x32.png')
img16 = Image.open('static/icons/favicon-16x16.png')

# Save as .ico with multiple sizes
img32.save('static/favicon.ico', format='ICO', sizes=[(16, 16), (32, 32)])

print('Created static/favicon.ico')
