from lxml import html
import re
import sys


# Script qui tente de mettre les mots d'un fichier HOCR dans le bon ordre
# Usage : python reorder_hocr.py <fichier_hocr>
# L'HOCR modifié sortira sur stdout

class BoundingBox:
    def __init__(self, title_attrib):
        fields = title_attrib.replace(";", "")
        toks = fields.split()
        bbox_start = toks.index("bbox")
        self.hpos = int(toks[bbox_start + 1])
        self.vpos = int(toks[bbox_start + 2])
        self.width = int(toks[bbox_start + 3])
        self.height = int(toks[bbox_start + 4])

    def as_tuple(self):
        return (self.hpos, self.vpos, self.width, self.height)

    def __repr__(self):
        return "bbox " + str(self.as_tuple())


class OCRLine:
    def __init__(self, element, index_in_parent):
        self.element = element
        self.bbox = BoundingBox(element.get("title"))
        self.index_in_parent = index_in_parent


def find_lines(html, index_in_parent=-1):
    result = []
    if html.get("class") == "ocr_line":
        result.append(OCRLine(html, index_in_parent))
    for i, c in enumerate(html):
        result += find_lines(c, i)
    return result


if len(sys.argv) != 2:
    print("Usage : python reorder_hocr.py <fichier_hocr>")
    exit()

# besoin de l'arbre pour reproduire le doctype en sortie
tree = html.parse(sys.argv[1])
root = tree.getroot()

lines = find_lines(root)

# Parfois il y a des lignes avec la bbox (0, 0, -1, -1), on les enlève
lines = [l for l in lines if l.bbox.as_tuple() != (0, 0, -1, -1)]

# Trouver la séquence la plus longue de ocr_line dont
# les vpos croissent
i = 0
j = 1
seq_start = 0
seq_end = 1
while j < len(lines):
    if lines[j].bbox.vpos < lines[j - 1].bbox.vpos:
        i = j
    j += 1
    if j - i > seq_end - seq_start:
        seq_start = i
        seq_end = j

for i, line in enumerate(lines):
    # Si cette ligne n'est pas dans le bon ordre,
    if i < seq_start or i >= seq_end:
        # Trouver où insérer cette ligne
        # j == seq_end - 1 dans deux cas :
        # 1. line doit être insérée à la fin du fichier
        # 2. line doit être insérée avant la dernière ligne du fichier
        j: int
        for j in range(seq_start, seq_end):
            if line.bbox.vpos < lines[j].bbox.vpos:
                break

        words_el = [x for x in line.element]

        # S'il y a une ligne précédante, il se peut qu'il y ait
        # des mots au début de cette ligne qui devraient figurer
        # dans la ligne précédante
        if j > 0 and len(lines[j - 1].element) > 0:

            word_preceding = lines[j - 1].element[-1]
            line_end_hpos = BoundingBox(word_preceding.get("title")).hpos

            for word_el in words_el:
                if BoundingBox(word_el.get("title")).hpos > line_end_hpos:
                    prec_el = lines[j - 1].element
                    prec_el.insert(len(prec_el), word_el)
                else:
                    break

        # S'il y a une ligne suivante, il se peut qu'il y ait des mots
        # à la fin de cette ligne qui devraient figurer dans la ligne
        # suivante
        if j < len(lines) - 1 and len(lines[j + 1].element) > 0:

            word_following = lines[j + 1].element[0]
            line_start_hpos = BoundingBox(word_following.get("title")).hpos

            for word_el in reversed(words_el):
                if BoundingBox(word_el.get("title")).hpos < line_start_hpos:
                    next_el = lines[j + 1].element
                    next_el.insert(0, word_el)
                else:
                    break

        old_parent = line.element.getparent()
        new_parent = lines[j].element.getparent()

        # lines[j].bbox.vpos < line.bbox.vpos dans le cas où
        # line doit être insérée après la dernière ligne du fichier
        # (j == seq_end - 1 dans ce cas)
        if lines[j].bbox.vpos > line.bbox.vpos:
            new_parent.insert(lines[j].index_in_parent, line.element)
        else:
            new_parent.insert(lines[j].index_in_parent + 1, line.element)

        # Supprimer d'éventuels éléments rendus vides par le
        # déplacement d'éléments
        while len(old_parent) == 0:
            old_parent_parent = old_parent.getparent()
            old_parent_parent.remove(old_parent)
            old_parent = old_parent_parent


def fix_meta_tags_old(mystr):
  mystr = mystr.replace('ocr-capabilities">', 'ocr-capabilities"/>')
  mystr = mystr.replace('ocr-system">', 'ocr-system"/>')
  mystr = mystr.replace('Content-Type">', 'Content-Type"/>')
  return mystr


metafix = re.compile(r"(<meta)([^>]+[^/])(\s*)(>)")


def fix_meta_tags(mystr):
  mystr = re.sub(metafix, r'\1\2/\3\4', mystr)
  return mystr


def is_xhtml(xmltree):
    return 'DOCTYPE html PUBLIC' in xmltree.docinfo.doctype


# reproduire entête pour avoir moins de diffs
TESSERACT_HEADER = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n\n"""
GIMAGE_HEADER = "<!DOCTYPE html>\n"

outstr = str(html.tostring(root, pretty_print=True, encoding='UTF-8'), encoding='UTF-8')

if is_xhtml(tree):
    outstr = TESSERACT_HEADER + outstr
else:
    outstr = GIMAGE_HEADER + outstr

print(fix_meta_tags(outstr.strip()))
