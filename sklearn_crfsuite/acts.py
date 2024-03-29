from html.parser import HTMLParser

import sklearn
from sklearn.metrics import make_scorer
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import RandomizedSearchCV

import sklearn_crfsuite
from sklearn_crfsuite import scorers
from sklearn_crfsuite import metrics

import pycrfsuite

import scipy

import sys
from lxml import etree
from lxml import html

import os

import re

import random

import time

from tei_gen import *

from collatex import *

from process_hocr import *
from process_alto import *
from process_common import *

from token_raw_data import *

from features import *

DEBUG = False

playname = ""
# Extraire les données brutes d'une pièce d'un ensemble de
# fichiers ALTO ou hOCR dans un dossier
def extract_play_data(play_dir):
  play = []
  i = 0

  global playname

  playname = os.path.basename(play_dir)

  for filename in sorted(os.listdir(play_dir)):
    #print(filename)
    if filename.endswith(".xml"):
      root = etree.parse(os.path.join(play_dir, filename)).getroot()
      # Layout, Page
      remove_page_number(root.find(
                        "{http://www.loc.gov/standards/alto/ns-v3#}Layout")
                        .find(
                        "{http://www.loc.gov/standards/alto/ns-v3#}Page"))

      n = extract_raw_data(root, get_fsizes(root))
      if len(n) > 0:
        n[0].page_num = i
      play += n
    elif filename.endswith(".html"):
      root = html.parse(os.path.join(play_dir, filename)).getroot()

      ignore_tags(root)

      remove_page_number_html(root)

      n = extract_raw_data_html(root)
      if len(n) > 0:
        n[0].page_num = i
      play += n
      for t in n:
        t.filename = filename
      
    i += 1
      
  # normaliser les hpos de la pièce
  max_hpos = max([t.hpos for t in play])
  for t in play:
    t.hpos /= max_hpos
    t.line_start_hpos /= max_hpos

  # normaliser les vpos de la pièce
  max_vpos = max([t.vpos for t in play])
  for t in play:
    t.vpos /= max_vpos

  # normaliser les tailles de caractères de la pièce
  max_fsize = max([t.fsize for t in play])
  for t in play:
    t.fsize /= max_fsize

  return play

# Trouver le texte correspondant à chaque token dans le fichier TEI
# Assortir ces tokens d'une étiquette selon l'élément dans lequel
# le texte correspondant apparaît (comme décrit pour get_labels ci-dessous)
def match_text(tokens, text, tag, labels, start_token, t_i, in_parent):

  c_i = 0
  text = finaggle(text)

  while c_i < len(text) and start_token < len(tokens):

    c = text[c_i]
    curr_str = tokens[start_token].string.replace("\n", "")

    if DEBUG:
      print(c, curr_str[t_i])

    # C'est le même caractère, on avance au prochain
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
    elif curr_str[t_i].isspace():
      t_i += 1
    else:
      if curr_str[t_i] not in '-:':
        print("ERROR: extraneous text in input data:", 
               bytes(curr_str[t_i], encoding="utf-8"))
        print("TOKEN:", tokens[start_token].string)
        print("Playname:", playname)
        print("Filename: ", tokens[start_token].filename)
        print("id: ", tokens[start_token].word_id)
        print(c, curr_str[t_i])

        context = text[max(0, c_i-10):c_i+15]

        print("CONTEXT: ", context + '%')
        exit()
      t_i += 1

    # On a atteint la fin de ce token
    if t_i == len(curr_str):
      # Il faut étiquetter ce token
      if in_parent and tag in labels:
        tokens[start_token] = (tokens[start_token], labels[tag])
      # Il ne faut pas l'étiquetter
      else:
        tokens[start_token] = (tokens[start_token], "O")
      start_token += 1

      if start_token == len(tokens):
        return start_token, 0

      assert(len(tokens[start_token].string) > 0)

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
    #for t in tei_body.text.split():
      #print("(", t)
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
    # Ignorer les italiques dans la TEI
    start_token, t_i = get_labels(tokens, child, parent, labels,
                             start_token=start_token, t_i=t_i,
                             in_parent=child_in_parent)

    # Chercher dans le texte après ce sous-élément
    if child.tail is not None:
      #for t in child.tail.split():
        #print("(", t)
      start_token, t_i = match_text(tokens, child.tail, tei_body.tag,
                               labels, start_token, t_i, in_parent)
  return start_token, t_i

def get_labels_acts(tokens, tei_body):
  act_div = etree.Element("{http://www.tei-c.org/ns/1.0}div", 
                          attrib={"type" : "act"})
  
  last_token, t_i = get_labels(tokens, tei_body, act_div,
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

def get_labels_stage_p(tokens, tei_body):
  parent = etree.Element("{http://www.tei-c.org/ns/1.0}stage", attrib={})
  
  get_labels(tokens, tei_body, parent, 
             {"{http://www.tei-c.org/ns/1.0}p" : "stage"})

def get_labels_div_p(tokens, tei_body):
  sp_parent = etree.Element("{http://www.tei-c.org/ns/1.0}div", attrib={})
  
  get_labels(tokens, tei_body, sp_parent, 
             {"{http://www.tei-c.org/ns/1.0}p" : "p"})

def get_labels_p(tokens, tei_body):

  sp_parent = etree.Element("{http://www.tei-c.org/ns/1.0}sp", attrib={})
  
  get_labels(tokens, tei_body, sp_parent, 
             {"{http://www.tei-c.org/ns/1.0}p" : "p"})

def get_labels_sp(tokens, tei_body):
  no_parent = etree.Element("NONE", attrib={})
  
  get_labels(tokens, tei_body, no_parent, 
             {"{http://www.tei-c.org/ns/1.0}sp" : "p"})

def get_labels_l(tokens, tei_body):
  no_parent = etree.Element("NONE", attrib={})
  
  get_labels(tokens, tei_body, no_parent, 
             {"{http://www.tei-c.org/ns/1.0}l" : "chanson"})

def get_labels_l_head(tokens, tei_body):
  lg = etree.Element("{http://www.tei-c.org/ns/1.0}lg", attrib={})
  
  get_labels(tokens, tei_body, lg, 
             {"{http://www.tei-c.org/ns/1.0}head" : "chanson"})

def get_play_data_all_labels(alto_dir, tei_file):
  tei_root = etree.parse(tei_file).getroot()
  
  tei_text = tei_root.find("{http://www.tei-c.org/ns/1.0}text")
  
  if tei_text is None:
    tei_body = tei_root.find("{http://www.tei-c.org/ns/1.0}body")
  else:
    tei_body = tei_text.find("{http://www.tei-c.org/ns/1.0}body")

  ignore_tags(tei_body)
  
  tokens = extract_play_data(alto_dir)
  
  assert(len(tokens) > 0)

  label_funcs = [get_labels_acts, get_labels_scenes, get_labels_speakers, 
                 get_labels_stage,  get_labels_p, get_labels_stage_p, 
                 get_labels_l, get_labels_l_head, get_labels_sp, get_labels_div_p]

  result = [(t, "O") for t in tokens]

  for f in label_funcs:
    f(tokens, tei_body)
    # TODO: this is garbage
    # Enlever les tokens non-étiquettés
    tokens = [t for t in tokens if not isinstance(t, TokenRawData)]
    result = result[0:len(tokens)]
    labels = [t[1] for t in tokens]
    tokens = [t[0] for t in tokens]
    for i in range(len(labels)):
      if labels[i] != "O":
        if result[i][1] != "O":
          print("Intersect:", labels[i], result[i][1])
        result[i] = (result[i][0], labels[i])
  
  #get_labels_stage(tokens, tei_body)

  #features = [features_default(tokens, i, 0.1) for i in range(len(tokens))]
  
  X = tokens
  Y = [tok[1] for tok in result]

  # Normalement, chaque token est étiquetté
  #print(Y)
  for i, y in enumerate(Y):
    if y == "O":
      print(X[i], "missing label")
      print(X[i-3:i+3])
    #assert(y != "O")

  assert(len(X) == len(Y))

  return X, Y

def find_heads(labels, tag):
  result = []
  last_tag = ""
  for i in range(len(labels)):
    y = labels[i]
    if y == tag and last_tag != tag:
      result.append(i)
    last_tag = y
  return result

def find_scene_heads(labels):
  return find_heads(labels, "scene_head")

def find_act_heads(labels):
  return find_heads(labels, "act_head")

# Choisir des tokens auxquels séparer une séquence
# en une partie test et une partie entrainement
def choose_rand_head(act_heads, scene_heads, len_seq):
  act_head = -1
  if len(act_heads) > 1:
    act_head = random.randrange(len(act_heads))

  scene_head = -1
  if len(scene_heads) > 1:
    scene_head = random.randrange(len(scene_heads))

  token = random.randrange(len_seq)

  return act_head, scene_head, token

def split_test_train(head_indices, heads, XYs):
  location = 0 

  X_train = []
  X_test = []
  Y_train = []
  Y_test = []

  for head_index, head, XY in zip(head_indices, heads, XYs):

    X, Y = XY
    #print(head_index)
    act_head, scene_head, token = head_index
    act_heads, scene_heads = head
    location = 0

    if act_head != -1:
      location = act_heads[act_head]
    elif scene_head != -1:
      location = scene_heads[scene_head]
    else:
      assert(token != -1)
      location = token

    percent_10 = len(X)//10

    start = location - percent_10//2
    end = location + percent_10//2

    if start < 0:
      start = 0
      end = percent_10
    elif end > len(X):
      end = len(X) 
      start = len(X) - percent_10

    # Ajuster start et end pour qu'ils se trouvent
    # au début d'un tour de parole
    while start > 0 and not (Y[start] == "speaker" and Y[start-1] != "speaker"):
      start -= 1

    while end < len(X) and not (Y[end] == "speaker" and Y[end-1] != "speaker"):
      end += 1

    X_train_before = X[0:start]
    Y_train_before = Y[0:start]

    X_test_n = X[start:end]
    Y_test_n = Y[start:end]

    X_train_after = X[end:len(X)]
    Y_train_after = Y[end:len(X)]

    if len(X_train_before) != 0:
      X_train.append(X_train_before)
      Y_train.append(Y_train_before)

    if len(X_train_after) != 0:
      X_train.append(X_train_after)
      Y_train.append(Y_train_after)

    X_test.append(X_test_n)
    Y_test.append(Y_test_n)

  assert(len(X_train) == len(Y_train))
  assert(len(X_test) == len(Y_test))

  return X_train, Y_train, X_test, Y_test

def get_data_sets():
  plays = [
           #"arnold-der-pfingstmontag", 
           "bastian-hofnarr-heidideldum", "clemens-chrischtowe", "greber-sainte-cecile", "hart-dr-poetisch-oscar", "jost-daa-im-narrehuss", "stoskopf-dr-hoflieferant", 
           "stoskopf-ins-ropfers-apothek",
           "schnockeloch",
           "charlot",
           "maischter",
           "yo-yo",
           "gift",
           "itzig",
           "paradies",
           "bureaukrate",
           "hochzittsreis",
           "oubli",
           "amerikaner",
           ]

  match_text_context = ""
  
  plays_XY = []
  
  for play in plays:
    print(os.path.join(sys.argv[1], play), os.path.join(sys.argv[2], play + ".xml"))
    X, Y = get_play_data_all_labels(os.path.join(sys.argv[1], play), os.path.join(sys.argv[2], play + ".xml"))
  
    print(play)
      
    #for x, y, in zip(X, Y):
    #    print(x, y, play)
  
    plays_XY.append((X, Y))
  
  act_heads = []
  scene_heads = []
  
  ###############################################################################
  # Division test/entrainement -------------------------------------------------#
  ###############################################################################
  
  for play in plays_XY:
    X, Y = play
  
    n_act_heads = find_act_heads(Y)
    n_scene_heads = find_scene_heads(Y)
  
    act_heads.append(n_act_heads)
    scene_heads.append(n_scene_heads)
  
    print(choose_rand_head(n_act_heads, n_scene_heads, len(Y)))
  
  # On enlève 10 pourcent des tours de paroles d'une pièce donnée autour du 
  # début d'un acte choisi au hasard (choisi par le code ci-dessus)
  # Pour les pièces qui n'ont qu'un seul acte, on choisit une scène à la place
  acts_remove = [2, -1, -1, -1, 0, 0, 1, 2, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1]
  scenes_remove = [-1, -1, 9, 5, -1, -1, -1, -1, 1, 5, 10, 10, 9, 2, 1, 6, 7, -1]
  random_remove = [-1, 3952, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]
  
  return split_test_train(
                      zip(acts_remove, scenes_remove, random_remove), 
                      zip(act_heads, scene_heads), plays_XY)
  
