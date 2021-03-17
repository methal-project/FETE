from itertools import chain

import sklearn
from sklearn.metrics import make_scorer
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import RandomizedSearchCV

import sklearn_crfsuite
from sklearn_crfsuite import scorers
from sklearn_crfsuite import metrics

import sys
from lxml import etree
import os

import re

def finaggle(s):
  return s.replace("‘", "'").replace("’", "'").replace("}", ")").replace("“","\"").replace("—","-").replace("”", "\"").replace("―", "-").replace("„", ",").replace("…", "...").replace("=", "-").replace("{", "(")

def fixquotes(tokens):
  last = False
  i = 0
  while i < len(tokens):
    if tokens[i] == "'":
      if last:
        tokens[i-1] = "“"
        tokens.pop(i)
        i -= 1
        last = False
      else:
        last = True
    else:
      last = False 
    i += 1

# Extraire le texte d'un élément XML en format ALTO
# TODO : extraire aussi les données de taille et d'indentation
# retourne une liste des tokens (<String>) trouvés dans l'élément donné
def extract_raw_data(node):
  result = []
  if node.tag == "{http://www.loc.gov/standards/alto/ns-v3#}String":
    result.append(finaggle(node.get("CONTENT")))
  for child in node:
    result += extract_raw_data(child) 
  return result

# Enlever le numéro de page en haut d'une page donnée
def remove_page_number(node):
  assert(node.tag == "{http://www.loc.gov/standards/alto/ns-v3#}Page")
  # PrintSpace, ComposedBlock, TextBlock, TextLine
  if len(node) < 1 or len(node[0]) < 1 or len(node[0][0]) < 1 or len(node[0][0][0]) < 1:
    return
  text_line = node[0][0][0][0]

  result = ""
  for string in text_line:
    result += string.get("CONTENT")

  if not bool(re.search('[A-Za-z]', result)):
    # Supprimer
    for string in text_line:
      string.set("CONTENT", "")
  
  
# Extraire les données brutes d'une pièce d'un ensemble de
# fichiers ALTO dans un dossier
def extract_play_data(play_dir):
  play = []
  for filename in os.listdir(sys.argv[1]):
    if filename.endswith(".xml"):
      root = etree.parse(os.path.join(sys.argv[1], filename)).getroot()
      # Layout, Page
      remove_page_number(root.find(
                        "{http://www.loc.gov/standards/alto/ns-v3#}Layout")
                        .find(
                        "{http://www.loc.gov/standards/alto/ns-v3#}Page"))
      play += extract_raw_data(root)
  return play

def match_text(tokens, text, tag, labels, start_token, t_i, in_parent):
  c_i = 0
  text = finaggle(text)
  while c_i < len(text) and start_token < len(tokens):
    c = text[c_i]
    print(c, tokens[start_token][t_i])
    if c == tokens[start_token][t_i]:
      t_i += 1
      c_i += 1
    elif c.isspace() or c == ":":
      c_i += 1
    else:
        print("Warning: extraneous text in ALTO :", tokens[start_token][t_i])
        t_i += 1
    if t_i == len(tokens[start_token]):
      if in_parent and tag in labels:
        tokens[start_token] = (tokens[start_token], labels[tag])
      else:
        tokens[start_token] = (tokens[start_token], "")
      start_token += 1
      while start_token < len(tokens) and len(tokens[start_token]) < 1:
        start_token += 1
      t_i = 0
  return start_token, t_i


# Assortir chaque token extrait d'une pièce d'une étiquette selon un
# fichier TEI de référence
# tokens : liste des tokens d'une pièce (modifiée avec les étiquettes)
# tei_body : élément <body> du fichier TEI de référence
# parent : élément dans lequel les étiquettes seront cherchées
# labels : dictionnaire envoyant un tag à l'étiquette dont
# le texte d'un élément avec ce tag sera assorti.
# les éléments n'existant pas dans ce dictionnaire seront assortis d'une
# étiquette vide
def get_labels(tokens, tei_body, parent, labels, 
               start_token=0, t_i=0, in_parent=False):
  if tei_body.text is not None:
    start_token, t_i = match_text(tokens, tei_body.text, tei_body.tag, 
                             labels, start_token, t_i, in_parent)
  
  # TODO : is this reference equality?
  child_in_parent = (tei_body.tag == parent.tag and 
                     tei_body.attrib == parent.attrib)

  for child in tei_body:
    start_token, t_i = get_labels(tokens, child, parent, labels,
                             start_token=start_token, t_i=t_i,
                             in_parent=child_in_parent)
    if child.tail is not None:
      start_token, t_i = match_text(tokens, child.tail, tei_body.tag,
                               labels, start_token, t_i, in_parent)
  return start_token, t_i

tei_root = etree.parse(sys.argv[2]).getroot()

tei_text = tei_root.find("{http://www.tei-c.org/ns/1.0}text")

tei_body = tei_text.find("{http://www.tei-c.org/ns/1.0}body")

tokens = extract_play_data(sys.argv[1])

fixquotes(tokens)

assert(len(tokens) > 0)

act_div = etree.Element("{http://www.tei-c.org/ns/1.0}div", attrib={"type" : "act"})

get_labels(tokens, tei_body, act_div, {"{http://www.tei-c.org/ns/1.0}head" : "act_head"})

print(tokens)


