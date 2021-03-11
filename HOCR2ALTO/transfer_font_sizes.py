from html.parser import HTMLParser
import sys
from lxml import etree

size_map = {}

class MyHTMLParser(HTMLParser):

  def handle_starttag(self, tag, attrs_):
    attrs = {}
    for k, v in attrs_:
      attrs[k] = v
    if tag == "span":
      if attrs["class"] == "ocr_line":
        title = attrs["title"]
        title_toks = title.split()
        fsize = float(title_toks[-1])
        self.curr_size = fsize
      elif attrs["class"] == "ocrx_word":
        size_map[attrs["id"]] = self.curr_size
    

parser = MyHTMLParser()
f = open(sys.argv[1])
parser.feed(f.read())
f.close()

root = etree.parse(sys.argv[2]).getroot()

unique_sizes = []
unique_size_map = {}
for size in size_map.values():
  if not (size in unique_sizes):
    unique_size_map[size] = len(unique_sizes)
    unique_sizes.append(size)

styles = etree.SubElement(root, "Styles")

for i in range(len(unique_sizes)):
  text_style = etree.SubElement(styles, "TextStyle")
  text_style.set("ID", "font" + str(i))
  text_style.set("FONTSIZE", str(unique_sizes[i]))
  # valeurs factices puisque Tesseract ne les fournit pas
  text_style.set("FONTFAMILY", "jbnolc+helvetica-bold")
  text_style.set("FONTTYPE", "sans-serif")
  text_style.set("FONTWIDTH", "proportional")
  text_style.set("FONTCOLOR", "#WWWWff")
  text_style.set("FONTSTYLE", "bold")

print(etree.tostring(root, pretty_print=True))
