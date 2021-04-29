from token_raw_data import *
from process_common import *
import re

# Extraire un dictionnaire qui envoie chaque styleref à sa taille
def get_fsizes(xml_doc):

  styles = xml_doc.find("{http://www.loc.gov/standards/alto/ns-v3#}Styles")
  if styles is None:
    print("Warning: missing font info for some files")
    return {}

  result = {}
  for text_style in styles:
    result[text_style.get("ID")] = float(text_style.get("FONTSIZE"))

  return result

# Extraire le texte d'un élément XML en format ALTO
def extract_raw_data(node, fsizes):

  result = []
  if node.tag == "{http://www.loc.gov/standards/alto/ns-v3#}TextLine":
    is_line_start = True
    line_start_hpos = 0
    for str_node in node: 
      string = finaggle(str_node.get("CONTENT"))

      if string.isspace() or string == '':
        continue

      assert(len(string) > 0)

      if DEBUG:
        print(str_node.attrib)

      hpos = 0
      if str_node.get("HPOS") is not None:
        hpos = int(str_node.get("HPOS"))

      if is_line_start:
        line_start_hpos = hpos

      if fsizes == {} or str_node.get("STYLEREFS") is None:
        fsize = 0.0 # Valeur factice qui signale le manque de données de taille
      else:
        fsize = fsizes[str_node.get("STYLEREFS")]

      # Some page numbers may have slipped
      string = re.sub("-[0-9]+-", "", string)
      n_token = TokenRawData(string, hpos, fsize, is_line_start, line_start_hpos, "")

      result.append(n_token)

      is_line_start = False
  else:
    for child in node:
      result += extract_raw_data(child, fsizes) 

  return result
      
def remove_page_number(node):

  for c in node:
    if c.tag == "{http://www.loc.gov/standards/alto/ns-v3#}TextLine":
      
      result = ""
      for string in c:
        result += string.get("CONTENT")


      if result.isspace() or result == "":
        continue

      if not bool(re.search('[A-Za-z]', result)):
        #print(result)
        # Supprimer
        for string in c:
          string.set("CONTENT", "")
        return True
    else:
      if remove_page_number(c):
        return True

  return False
