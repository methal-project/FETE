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

DEBUG = False

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

class TokenRawData:
  def __init__(self, string, hpos, fsize):
    self.string = string
    self.hpos = hpos
    self.fsize = fsize

  def __str__(self):
    return ("('" + self.string + "', " + str(self.hpos) + ", " + 
                                          str(self.fsize) + ")")
 
  def __repr__(self):
    return str(self)

INCREASE = "INCREASE"
CONSTANT = "CONSTANT"
DECREASE = "DECREASE"

def features_default(raw_tokens, i, indent_threshold):
  word = raw_tokens[i].string

  fsize = CONSTANT
  if i > 0:
    if raw_tokens[i].fsize > raw_tokens[i-1].fsize:
      fsize = INCREASE
    elif raw_tokens[i].fsize < raw_tokens[i-1].fsize:
      fsize = DECREASE
    
  features = {
    'word': word,
    'word.lower()': word.lower(),
    'word[0].isupper()': word[0].isupper(),
    'indent': CONSTANT, # TODO
    'fsize': fsize,
    'word_contains_period' : '.' in word,
    'word_contains_colon' : ':' in word,
    'word_contains_lparen' : '(' in word,
    'word_contains_rparen' : ')' in word, 
    'word_contains_digit' : bool(re.search('[0-9]', word)),
     # Autres idées : est-ce que le mot contient des diacritiques présents seulement en alsacien/français ?
     # Je pense que les auteurs font usage de tous les diacritiques allemands en écrivant l'alsacien
  }

# TODO : est-ce que tous ces remplacements sont nécessaires / souhaitables ?
def finaggle(s):
  return s.replace("‘", "'").replace("’", "'").replace("}", ")").replace("“","\"").replace("—","-").replace("”", "\"").replace("―", "-").replace("„", ",").replace("…", "...").replace("=", "-").replace("{", "(")


# Extraire le texte d'un élément XML en format ALTO
# TODO : extraire aussi les données de taille et d'indentation
# retourne une liste des tokens (<String>) trouvés dans l'élément donné
def extract_raw_data(node, fsizes):

  result = []
  if node.tag == "{http://www.loc.gov/standards/alto/ns-v3#}String":
    string = finaggle(node.get("CONTENT"))

    if string.isspace() or string == '':
      print("Warning: empty token, ignoring")
      return result

    if DEBUG:
      print(node.attrib)

    hpos = int(node.get("HPOS"))

    if fsizes == {}:
      fsize = 0.0 # Valeur factice qui signale le manque de données de taille
    else:
      fsize = fsizes[node.get("STYLEREFS")]

    n_token = TokenRawData(string, hpos, fsize)

    result.append(n_token)

  for child in node:
    result += extract_raw_data(child, fsizes) 

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
      string.set("CONTENT", " ")
  
  
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
      play += extract_raw_data(root, get_fsizes(root))
  return play

# Trouver le texte correspondant à chaque token dans le fichier TEI
# Assortir ces tokens d'une étiquette selon l'élément dans lequel
# le texte correspondant apparaît (comme décrit pour get_labels ci-dessous)
def match_text(tokens, text, tag, labels, start_token, t_i, in_parent):

  c_i = 0
  text = finaggle(text)

  while c_i < len(text) and start_token < len(tokens):

    c = text[c_i]
    curr_str = tokens[start_token].string

    if DEBUG:
      print(c, curr_str[t_i])

    # C'est le même caractèee, on avance au prochain
    if c == curr_str[t_i]:
      t_i += 1
      c_i += 1
    # On saute les espaces supplémentaires dans le TEI
    # TODO : Les deux-points sont souvent mal alignés ...
    elif c.isspace() or c == ":":
      c_i += 1
    # On a trouvé un caractère qui existe dans l'ALTO mais pas dans le TEI
    # On le saute en espérant pouvoir continuer
    # (Cela peut arriver avec les numéros de page par exemple)
    else:
        if DEBUG:
          print("Warning: extraneous text in ALTO :", tokens[start_token][t_i])
        t_i += 1

    # On a atteint la fin de ce token
    if t_i == len(curr_str):
      # Il faut étiquetter ce token
      if in_parent and tag in labels:
        tokens[start_token] = (tokens[start_token], labels[tag])
      # Il ne faut pas l'étiquetter
      else:
        tokens[start_token] = (tokens[start_token], "")
      start_token += 1

      # Sauter les tokens vides
      while start_token < len(tokens) and len(tokens[start_token].string) < 1:
        start_token += 1

      if start_token == len(tokens):
        return start_token, 0

      curr_token = tokens[start_token].string
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

  # Chercher dans le texte au-dessus des éléments
  if tei_body.text is not None:
    start_token, t_i = match_text(tokens, tei_body.text, tei_body.tag, 
                             labels, start_token, t_i, in_parent)
  
  # Est-ce que l'élément en cours de traitement est le parent recherché ?
  child_in_parent = tei_body.tag == parent.tag or parent.tag == "NONE"
  for attr in parent.attrib:
    if tei_body.get(attr) != parent.get(attr):
      child_in_parent = False

  # Itérer à travers les sous-éléments
  for child in tei_body:
    # Chercher dans ce sous-élément
    start_token, t_i = get_labels(tokens, child, parent, labels,
                             start_token=start_token, t_i=t_i,
                             in_parent=child_in_parent)

    # Chercher dans le texte après ce sous-élément
    if child.tail is not None:
      start_token, t_i = match_text(tokens, child.tail, tei_body.tag,
                               labels, start_token, t_i, in_parent)
  return start_token, t_i

def get_labels_acts(tokens, tei_body):
  act_div = etree.Element("{http://www.tei-c.org/ns/1.0}div", 
                          attrib={"type" : "act"})
  
  get_labels(tokens, tei_body, act_div, 
             {"{http://www.tei-c.org/ns/1.0}head" : "act_head"})

def get_labels_scenes(tokens, tei_body):
  scene_div = etree.Element("{http://www.tei-c.org/ns/1.0}div", 
                            attrib={"type" : "scene"})
  
  get_labels(tokens, tei_body, scene_div, 
             {"{http://www.tei-c.org/ns/1.0}head" : "scene_head"})

def get_labels_speakers(tokens, tei_body):
  sp_div = etree.Element("{http://www.tei-c.org/ns/1.0}sp", attrib={})
  
  get_labels(tokens, tei_body, sp_div, 
             {"{http://www.tei-c.org/ns/1.0}speaker" : "speaker"})

def get_labels_stage(tokens, tei_body):
  no_parent = etree.Element("NONE", attrib={})
  
  get_labels(tokens, tei_body, no_parent, 
             {"{http://www.tei-c.org/ns/1.0}stage" : "stage"}, in_parent=True)


tei_root = etree.parse(sys.argv[2]).getroot()

tei_text = tei_root.find("{http://www.tei-c.org/ns/1.0}text")

tei_body = tei_text.find("{http://www.tei-c.org/ns/1.0}body")

tokens = extract_play_data(sys.argv[1])

assert(len(tokens) > 0)

get_labels_stage(tokens, tei_body)

print(tokens)

