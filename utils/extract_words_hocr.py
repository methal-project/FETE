"""Extracts text of elements with @class ocrx_word given HOCR input"""

from lxml import html
import sys

root = html.parse(sys.argv[1]).getroot()

def print_words(html):
  if html.get("class") == "ocrx_word":
    if html.text is not None:
      print(html.text)
  for c in html:
    print_words(c)

print_words(root)
