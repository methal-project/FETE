from html.parser import HTMLParser
import sys
from lxml import etree

# Transfère les tailles de police contenues dans un fichier
# HOCR au fichier ALTO crée par ocr-transform à partir de ce fichier
# HOCR
# Utile puisque ocr-transform ignore ces informations

size_map = {}

class MyHTMLParser(HTMLParser):

  def handle_starttag(self, tag, attrs_):
    # récolter les attributs sous forme de dictionnaire
    attrs = {}
    for k, v in attrs_:
      attrs[k] = v

    if tag == "span":
      if (attrs["class"] == "ocr_line" or attrs["class"] == "ocr_header" or
          attrs["class"] == "ocr_textfloat" or attrs["class"] == "ocr_caption"):
        title = attrs["title"]
        title_toks = title.split()

        # extraire le dernier token délimité par des espaces, c'est le
        # numéro qui suit "x_size" dans les fichiers que produit Tesseract
        fsize = float(title_toks[-1])

        self.curr_size = fsize
      elif attrs["class"] == "ocrx_word":
        # La taille de ce mot est la dernière taille qu'on a vue dans un tag
        # ocr_line
        size_map[attrs["id"]] = self.curr_size
    

parser = MyHTMLParser()
f = open(sys.argv[1])
parser.feed(f.read())
f.close()

root = etree.parse(sys.argv[2]).getroot()

# Liste des tailles de police qui existent dans le fichier
unique_sizes = []
# Envoie chaque ID à sa taille de police
unique_size_map = {}
for size in size_map.values():
  if not (size in unique_sizes):
    unique_size_map[size] = len(unique_sizes)
    unique_sizes.append(size)


# Insérer un élément Styles pour stocker
# les différentes tailles dont on aura besoin
styles = etree.Element("Styles")
root.insert(1, styles)

# Créer les styles
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

def insert_font_sizes(node):
  if node.tag == "{http://www.loc.gov/standards/alto/ns-v3#}String":
    node.set("STYLEREFS", "font" + str(unique_size_map[size_map[node.get("ID")]]))
  for child in node:
    insert_font_sizes(child)

insert_font_sizes(root)

f = open(sys.argv[2], "wb")
f.write(etree.tostring(root, pretty_print=True))
f.close()
