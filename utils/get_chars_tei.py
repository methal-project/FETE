from lxml import etree

import sys

root = etree.parse(sys.argv[1]).getroot() 

def print_persName(root):
  if root.tag == "{http://www.tei-c.org/ns/1.0}persName":
    print(root.text.strip().replace("\n", "").replace("\t", ""))
  for child in root:
    print_persName(child)

print_persName(root)
