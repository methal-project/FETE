from itertools import chain

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
  def __init__(self, string, hpos, fsize, is_line_start, line_start_hpos):
    self.string = string
    self.hpos = hpos
    self.fsize = fsize
    self.is_line_start = is_line_start
    self.line_start_hpos = line_start_hpos
    self.page_num = -1

  def __str__(self):
    return ("('" + self.string + "', " + str(self.hpos) + ", " + 
                                          str(self.fsize) + ")") # TODO
 
  def __repr__(self):
    return str(self)

INCREASE = "INCREASE"
CONSTANT = "CONSTANT"
DECREASE = "DECREASE"

def only_alpha(word):
  return re.sub('[^A-Za-zè]', '', word)

def features_no_context(raw_tokens, i, indent_threshold):
  word = raw_tokens[i].string

  fsize = CONSTANT
  if i > 0:
    if raw_tokens[i].fsize > raw_tokens[i-1].fsize:
      fsize = INCREASE
    elif raw_tokens[i].fsize < raw_tokens[i-1].fsize:
      fsize = DECREASE

  line_start_hpos = raw_tokens[i].line_start_hpos

  # Trouver le début de la ligne précédante
  j = i
  in_last_line = False
  last_line_start_hpos = -1
  while j >= 0:
    if in_last_line:
      last_line_start_hpos = raw_tokens[j].line_start_hpos
      break
    else:
      if raw_tokens[j].is_line_start:
        in_last_line = True
    j -= 1

  indent = CONSTANT
  if last_line_start_hpos != -1:
    if line_start_hpos - last_line_start_hpos > indent_threshold:
      indent = INCREASE
    elif line_start_hpos - last_line_start_hpos < -indent_threshold:
      indent = DECREASE

  def is_acty(word):
    lex = ['akt', 'bild', 'aufzug']
    result = False
    oa = only_alpha(word.lower())
    for l in lex:
      result = result or l == oa
    
    return result

  def is_sceney(word):
    lex = ['ufftritt', 'scène', 'szene']
    result = False
    oa = only_alpha(word.lower())
    for l in lex:
      result = result or l == oa
    
    return result

  def is_rom_num(word):
    result = True
    oa = only_alpha(word.lower())
    for c in oa:
      result = result and c in 'ivx'
    return result

  features = {
    'word': word,
    'line_start': raw_tokens[i].is_line_start,
    'word.lower()': word.lower(),
    'word[0].isupper()': word[0].isupper(),
    'indent': indent,
    'fsize': fsize,
    'word_contains_period' : '.' in word,
    'word_contains_colon' : ':' in word,
    'word_contains_lparen' : '(' in word,
    'word_contains_rparen' : ')' in word, 
    'word_contains_digit' : bool(re.search('[0-9]', word)),
    'word_is_acty' : is_acty(word),
    'word_is_sceney' : is_sceney(word),
    'word_rom_num' : is_rom_num(word),
    'hpos' : raw_tokens[i].hpos,
     # Autres idées : est-ce que le mot contient des diacritiques présents seulement en alsacien/français ?
     # Je pense que les auteurs font usage de tous les diacritiques allemands en écrivant l'alsacien
     # Premier mot d'une page ?
  }

  return features

def features_no_lex(raw_tokens, i, indent_threshold):
  word = raw_tokens[i].string

  fsize = CONSTANT
  if i > 0:
    if raw_tokens[i].fsize > raw_tokens[i-1].fsize:
      fsize = INCREASE
    elif raw_tokens[i].fsize < raw_tokens[i-1].fsize:
      fsize = DECREASE

  line_start_hpos = raw_tokens[i].line_start_hpos

  # Trouver le début de la ligne précédante
  j = i
  in_last_line = False
  last_line_start_hpos = -1
  while j >= 0:
    if in_last_line:
      last_line_start_hpos = raw_tokens[j].line_start_hpos
      break
    else:
      if raw_tokens[j].is_line_start:
        in_last_line = True
    j -= 1

  indent = CONSTANT
  if last_line_start_hpos != -1:
    if line_start_hpos - last_line_start_hpos > indent_threshold:
      indent = INCREASE
    elif line_start_hpos - last_line_start_hpos < -indent_threshold:
      indent = DECREASE

  def is_acty(word):
    lex = ['akt', 'bild', 'aufzug']
    result = False
    oa = only_alpha(word.lower())
    for l in lex:
      result = result or l == oa
    
    return result

  def is_sceney(word):
    lex = ['ufftritt', 'scène', 'szene']
    result = False
    oa = only_alpha(word.lower())
    for l in lex:
      result = result or l == oa
    
    return result

  def is_rom_num(word):
    result = True
    oa = only_alpha(word.lower())
    for c in oa:
      result = result and c in 'ivx'
    return result

  features = {
    'word': word,
    'line_start': raw_tokens[i].is_line_start,
    'word.lower()': word.lower(),
    'word[0].isupper()': word[0].isupper(),
    'indent': indent,
    'fsize': fsize,
    'word_contains_period' : '.' in word,
    'word_contains_colon' : ':' in word,
    'word_contains_lparen' : '(' in word,
    'word_contains_rparen' : ')' in word, 
    'word_contains_digit' : bool(re.search('[0-9]', word)),
    'word_rom_num' : is_rom_num(word),
    'hpos' : raw_tokens[i].hpos,
     # Autres idées : est-ce que le mot contient des diacritiques présents seulement en alsacien/français ?
     # Je pense que les auteurs font usage de tous les diacritiques allemands en écrivant l'alsacien
     # Premier mot d'une page ?
  }

  if i > 0:
    word1 = raw_tokens[i-1].string
    features.update({
      '-1word': word1,
      '-1line_start': raw_tokens[i-1].is_line_start,
      '-1word.lower()': word1.lower(),
      '-1word[0].isupper()': word1[0].isupper(),
      '-1word_contains_period' : '.' in word1,
      '-1word_contains_colon' : ':' in word1,
      '-1word_contains_lparen' : '(' in word1,
      '-1word_contains_rparen' : ')' in word1, 
      '-1word_contains_digit' : bool(re.search('[0-9]', word1)),
      '-1word_rom_num' : is_rom_num(word1),
      '-1hpos' : raw_tokens[i-1].hpos,
    }) 

  if i < len(raw_tokens)-1:
    word1 = raw_tokens[i+1].string
    features.update({
      '+1word': word1,
      '+1line_start': raw_tokens[i+1].is_line_start,
      '+1word.lower()': word1.lower(),
      '+1word[0].isupper()': word1[0].isupper(),
      '+1word_contains_period' : '.' in word1,
      '+1word_contains_colon' : ':' in word1,
      '+1word_contains_lparen' : '(' in word1,
      '+1word_contains_rparen' : ')' in word1, 
      '+1word_contains_digit' : bool(re.search('[0-9]', word1)),
      '+1word_rom_num' : is_rom_num(word1),
      '+1hpos' : raw_tokens[i+1].hpos,
    }) 

  return features

def features_syl(raw_tokens, i, indent_threshold):
  word = raw_tokens[i].string

  fsize = CONSTANT
  if i > 0:
    if raw_tokens[i].fsize > raw_tokens[i-1].fsize:
      fsize = INCREASE
    elif raw_tokens[i].fsize < raw_tokens[i-1].fsize:
      fsize = DECREASE

  line_start_hpos = raw_tokens[i].line_start_hpos

  line_end = i
  # Trouver la fin de la ligne
  while line_end < len(raw_tokens) - 1:
    if raw_tokens[line_end + 1].is_line_start:
      break
    line_end += 1

  next_line_end = line_end + 1
  while next_line_end < len(raw_tokens) - 1:
    if raw_tokens[next_line_end + 1].is_line_start:
      break
    next_line_end += 1

  # Trouver le début de la ligne précédante
  j = i
  in_last_line = False
  last_line_start_hpos = -1
  last_line_end : int
  while j >= 0:
    if in_last_line:
      last_line_start_hpos = raw_tokens[j].line_start_hpos
      break
    else:
      if raw_tokens[j].is_line_start:
        in_last_line = True
    j -= 1
 
  last_line_end = j

  last_line_start = last_line_end
  while last_line_start >= 0:
    if raw_tokens[last_line_start].is_line_start:
      break
    last_line_start -= 1

  next_line_start = line_end + 1

  line_start = last_line_end + 1

  indent = CONSTANT
  if last_line_start_hpos != -1:
    if line_start_hpos - last_line_start_hpos > indent_threshold:
      indent = INCREASE
    elif line_start_hpos - last_line_start_hpos < -indent_threshold:
      indent = DECREASE

  def is_acty(word):
    lex = ['akt', 'bild', 'aufzug']
    result = False
    oa = only_alpha(word.lower())
    for l in lex:
      result = result or l == oa
    
    return result

  def is_sceney(word):
    lex = ['ufftritt', 'scène', 'szene']
    result = False
    oa = only_alpha(word.lower())
    for l in lex:
      result = result or l == oa
    
    return result

  def is_rom_num(word):
    result = True
    oa = only_alpha(word.lower())
    for c in oa:
      result = result and c in 'ivx'
    return result

  features = {
    'word': word,
    'line_start': raw_tokens[i].is_line_start,
    'word.lower()': word.lower(),
    'word[0].isupper()': word[0].isupper(),
    'indent': indent,
    'fsize': fsize,
    'word_contains_period' : '.' in word,
    'word_contains_colon' : ':' in word,
    'word_contains_lparen' : '(' in word,
    'word_contains_rparen' : ')' in word, 
    'word_contains_digit' : bool(re.search('[0-9]', word)),
    'word_is_acty' : is_acty(word),
    'word_is_sceney' : is_sceney(word),
    'word_rom_num' : is_rom_num(word),
    'hpos' : raw_tokens[i].hpos,
    'fsize_norm' : raw_tokens[i].fsize,
    'line_end_hpos' : raw_tokens[line_end].hpos,
     # Autres idées : est-ce que le mot contient des diacritiques présents seulement en alsacien/français ?
     # Je pense que les auteurs font usage de tous les diacritiques allemands en écrivant l'alsacien
     # Premier mot d'une page ?
  }

  if i > 0:
    word1 = raw_tokens[i-1].string
    features.update({
      '-1word': word1,
      '-1line_start': raw_tokens[i-1].is_line_start,
      '-1word.lower()': word1.lower(),
      '-1word[0].isupper()': word1[0].isupper(),
      '-1word_contains_period' : '.' in word1,
      '-1word_contains_colon' : ':' in word1,
      '-1word_contains_lparen' : '(' in word1,
      '-1word_contains_rparen' : ')' in word1, 
      '-1word_contains_digit' : bool(re.search('[0-9]', word1)),
      '-1word_is_acty' : is_acty(word1),
      '-1word_is_sceney' : is_sceney(word1),
      '-1word_rom_num' : is_rom_num(word1),
      '-1hpos' : raw_tokens[i-1].hpos,
    }) 

  if i < len(raw_tokens)-1:
    word1 = raw_tokens[i+1].string
    features.update({
      '+1word': word1,
      '+1line_start': raw_tokens[i+1].is_line_start,
      '+1word.lower()': word1.lower(),
      '+1word[0].isupper()': word1[0].isupper(),
      '+1word_contains_period' : '.' in word1,
      '+1word_contains_colon' : ':' in word1,
      '+1word_contains_lparen' : '(' in word1,
      '+1word_contains_rparen' : ')' in word1, 
      '+1word_contains_digit' : bool(re.search('[0-9]', word1)),
      '+1word_is_acty' : is_acty(word1),
      '+1word_is_sceney' : is_sceney(word1),
      '+1word_rom_num' : is_rom_num(word1),
      '+1hpos' : raw_tokens[i+1].hpos,
    }) 

    if next_line_end != line_end and next_line_end < len(raw_tokens):

      this_word = re.sub('[!"\,\.\?]', '', raw_tokens[line_end].string)
      next_word = re.sub('[!"\,\.\?]', '', raw_tokens[next_line_end].string)

      if len(this_word) > 0 and len(next_word) > 0:

        features.update({
          '+1rhyme_1' : this_word[-1] == next_word[-1],
          '+1rhyme_2' : this_word[-2:] == next_word[-2:],
          '+1rhyme_3' : this_word[-3:] == next_word[-3:], 
          '+1line_end_hpos' : raw_tokens[next_line_end].hpos,
        })

    if last_line_end != line_end and last_line_end >= 0:

      this_word = re.sub('[!"\,\.\?]', '', raw_tokens[last_line_end].string)
      next_word = re.sub('[!"\,\.\?]', '', raw_tokens[line_end].string)

      if len(this_word) > 0 and len(next_word) > 0:

        features.update({
          '-1rhyme_1' : this_word[-1] == next_word[-1],
          '-1rhyme_2' : this_word[-2:] == next_word[-2:],
          '-1rhyme_3' : this_word[-3:] == next_word[-3:], 
          '-1line_end_hpos' : raw_tokens[last_line_end].hpos,
        })

    def approx_nuclei(line):
      line = " ".join([x.string for x in line])
      count = 0
      in_nucleus = False
      for c in line:
        if c.lower() in "aeiouàèìòùáéíóúäöüïëâêîûô":
          if not in_nucleus:
            count += 1
            in_nucleus = True
        else:
          in_nucleus = False
      return count

    curr_line_nuc = approx_nuclei(raw_tokens[line_start:next_line_start])

    if next_line_start < len(raw_tokens):
      next_line_nuc = approx_nuclei(raw_tokens[next_line_start:next_line_end + 1])
      features.update({'+1syl_diff' : abs(curr_line_nuc - next_line_nuc)})

    if last_line_start >= 0:
      last_line_nuc = approx_nuclei(raw_tokens[last_line_start:line_start])
      features.update({'-1syl_diff' : abs(curr_line_nuc - last_line_nuc)})

  return features

def features_default(raw_tokens, i, indent_threshold):
  word = raw_tokens[i].string

  fsize = CONSTANT
  if i > 0:
    if raw_tokens[i].fsize > raw_tokens[i-1].fsize:
      fsize = INCREASE
    elif raw_tokens[i].fsize < raw_tokens[i-1].fsize:
      fsize = DECREASE

  line_start_hpos = raw_tokens[i].line_start_hpos

  # Trouver le début de la ligne précédante
  j = i
  in_last_line = False
  last_line_start_hpos = -1
  while j >= 0:
    if in_last_line:
      last_line_start_hpos = raw_tokens[j].line_start_hpos
      break
    else:
      if raw_tokens[j].is_line_start:
        in_last_line = True
    j -= 1

  indent = CONSTANT
  if last_line_start_hpos != -1:
    if line_start_hpos - last_line_start_hpos > indent_threshold:
      indent = INCREASE
    elif line_start_hpos - last_line_start_hpos < -indent_threshold:
      indent = DECREASE

  def is_acty(word):
    lex = ['akt', 'bild', 'aufzug']
    result = False
    oa = only_alpha(word.lower())
    for l in lex:
      result = result or l == oa
    
    return result

  def is_sceney(word):
    lex = ['ufftritt', 'scène', 'szene']
    result = False
    oa = only_alpha(word.lower())
    for l in lex:
      result = result or l == oa
    
    return result

  def is_rom_num(word):
    result = True
    oa = only_alpha(word.lower())
    for c in oa:
      result = result and c in 'ivx'
    return result

  features = {
    'word': word,
    'line_start': raw_tokens[i].is_line_start,
    'word.lower()': word.lower(),
    'word[0].isupper()': word[0].isupper(),
    'indent': indent,
    'fsize': fsize,
    'word_contains_period' : '.' in word,
    'word_contains_colon' : ':' in word,
    'word_contains_lparen' : '(' in word,
    'word_contains_rparen' : ')' in word, 
    'word_contains_digit' : bool(re.search('[0-9]', word)),
    'word_is_acty' : is_acty(word),
    'word_is_sceney' : is_sceney(word),
    'word_rom_num' : is_rom_num(word),
    'hpos' : raw_tokens[i].hpos,
    'fsize_norm' : raw_tokens[i].fsize
     # Autres idées : est-ce que le mot contient des diacritiques présents seulement en alsacien/français ?
     # Je pense que les auteurs font usage de tous les diacritiques allemands en écrivant l'alsacien
     # Premier mot d'une page ?
  }

  if i > 0:
    word1 = raw_tokens[i-1].string
    features.update({
      '-1word': word1,
      '-1line_start': raw_tokens[i-1].is_line_start,
      '-1word.lower()': word1.lower(),
      '-1word[0].isupper()': word1[0].isupper(),
      '-1word_contains_period' : '.' in word1,
      '-1word_contains_colon' : ':' in word1,
      '-1word_contains_lparen' : '(' in word1,
      '-1word_contains_rparen' : ')' in word1, 
      '-1word_contains_digit' : bool(re.search('[0-9]', word1)),
      '-1word_is_acty' : is_acty(word1),
      '-1word_is_sceney' : is_sceney(word1),
      '-1word_rom_num' : is_rom_num(word1),
      '-1hpos' : raw_tokens[i-1].hpos,
    }) 

  if i < len(raw_tokens)-1:
    word1 = raw_tokens[i+1].string
    features.update({
      '+1word': word1,
      '+1line_start': raw_tokens[i+1].is_line_start,
      '+1word.lower()': word1.lower(),
      '+1word[0].isupper()': word1[0].isupper(),
      '+1word_contains_period' : '.' in word1,
      '+1word_contains_colon' : ':' in word1,
      '+1word_contains_lparen' : '(' in word1,
      '+1word_contains_rparen' : ')' in word1, 
      '+1word_contains_digit' : bool(re.search('[0-9]', word1)),
      '+1word_is_acty' : is_acty(word1),
      '+1word_is_sceney' : is_sceney(word1),
      '+1word_rom_num' : is_rom_num(word1),
      '+1hpos' : raw_tokens[i+1].hpos,
    }) 

  return features

def finaggle(s):
  return s.replace("‘", "'").replace("’", "'").replace("}", ")").replace("“","\"").replace("—","-").replace("”", "\"").replace("―", "-").replace("„", "\"").replace("…", "...").replace("=", "-").replace("{", "(")


# Extraire le texte d'un élément XML en format ALTO
# retourne une liste des tokens (<String>) trouvés dans l'élément donné
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

      n_token = TokenRawData(string, hpos, fsize, is_line_start, line_start_hpos)

      result.append(n_token)

      is_line_start = False
  else:
    for child in node:
      result += extract_raw_data(child, fsizes) 

  return result

def extract_raw_data_html(node, font_size=0.0, is_line_start=False, line_start_hpos=0.0):
  result = []
  if node.tag == "span":
    cl = node.get("class")
    if cl == "ocr_line":
      title = node.get("title")
      title = title.replace(";", "").split()
      idx = title.index("x_size")
      font_size = float(title[idx + 1])
      is_line_start = True
    elif cl == "ocrx_word":
      if node.text is not None:
        content = finaggle(node.text)
        if content.isspace() or content == '':
          return []
        title = node.get("title")
        title = title.replace(";", "").split()
        bbox = title.index("bbox")
        hpos = int(title[bbox + 1])
        n_token = TokenRawData(content, hpos, font_size, is_line_start, 
                               line_start_hpos)
        result.append(n_token)
  
  for c in node:
    result += extract_raw_data_html(c, font_size=font_size, 
                                    is_line_start=is_line_start,
                                    line_start_hpos=line_start_hpos)
    if len(result) > 0:
      if is_line_start:
        line_start_hpos = result[-1].hpos
        result[-1].line_start_hpos = result[-1].hpos
    is_line_start = False

  return result
      

# Enlever le numéro de page en haut d'une page donnée
#def remove_page_number(node):
#  assert(node.tag == "{http://www.loc.gov/standards/alto/ns-v3#}Page")
#  # PrintSpace, ComposedBlock, TextBlock, TextLine
#  if len(node) < 1 or len(node[0]) < 1 or len(node[0][0]) < 1 or len(node[0][0][0]) < 1:
#    return
#  text_line = node[0][0][0][0]
#
#  result = ""
#  for string in text_line:
#    result += string.get("CONTENT")
#
#  if not bool(re.search('[A-Za-z]', result)):
#    # Supprimer
#    for string in text_line:
#      string.set("CONTENT", "")

def remove_page_number(node):

  for c in node:
    if c.tag == "{http://www.loc.gov/standards/alto/ns-v3#}TextLine":
      
      result = ""
      for string in c:
        result += string.get("CONTENT")


      if result.isspace() or result == "":
        continue

      if not bool(re.search('[A-Za-z]', result)):
        print(result)
        # Supprimer
        for string in c:
          string.set("CONTENT", "")
        return True
    else:
      if remove_page_number(c):
        return True

  return False

def remove_page_number_html(node):
  for c in node:
    if c.tag == "span" and c.get("class") == "ocrx_line":

      result = ""
      for string in c:
        result += string.text

      if result.isspace() or result == "":
        continue

      if not bool(re.search('[A-Za-z]', result)):
        print(result)
        # Supprimer
        for string in c:
          string.text = ""
        return True
    else:
      if remove_page_number(c):
        return True

  return False
  
# Extraire les données brutes d'une pièce d'un ensemble de
# fichiers ALTO ou hOCR dans un dossier
def extract_play_data(play_dir):
  play = []
  i = 0
  for filename in sorted(os.listdir(play_dir)):
    print(filename)
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
      
    i += 1
      
  # normaliser les hpos de la pièce
  max_hpos = max([t.hpos for t in play])
  for t in play:
    t.hpos /= max_hpos
    t.line_start_hpos /= max_hpos

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
    curr_str = tokens[start_token].string

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
    else:
        if curr_str[t_i] not in ':-!;' and True:
          print("Warning: extraneous text in ALTO :", curr_str[t_i])
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

def get_labels_p(tokens, tei_body):
  sp_parent = etree.Element("{http://www.tei-c.org/ns/1.0}sp", attrib={})
  
  get_labels(tokens, tei_body, sp_parent, 
             {"{http://www.tei-c.org/ns/1.0}p" : "p"})

def get_labels_l(tokens, tei_body):
  no_parent = etree.Element("NONE", attrib={})
  
  get_labels(tokens, tei_body, no_parent, 
             {"{http://www.tei-c.org/ns/1.0}l" : "chanson"})

# Ignorer les éléments seg, emph et span
def ignore_tags(root):
  removals = set()
  for i in range(len(root) - 1, -1, -1):
    #print(i, root[i].tag)
    if (root[i].tag == "{http://www.tei-c.org/ns/1.0}emph" 
       or root[i].tag == "{http://www.tei-c.org/ns/1.0}seg"
       or root[i].tag == "{http://www.tei-c.org/ns/1.0}span"
       or root[i].tag == "strong"):
      #print(etree.ElementTree.dump(root[i]))
      if i > 0:
        if root[i-1].tail is None:
          root[i-1].tail = ""
        if root[i].text is not None:
          root[i-1].tail += root[i].text
        if root[i].tail is not None:
          root[i-1].tail += root[i].tail
      else:
        if root.text is None:
          root.text = ""
        if root[i].text is not None:
          root.text += root[i].text
        if root[i].tail is not None:
          root.text += root[i].tail
      removals.add(root[i])

  for r in removals:
    root.remove(r)

  for child in root:
    ignore_tags(child)

def get_play_data_all_labels(alto_dir, tei_file):
  tei_root = etree.parse(tei_file).getroot()
  
  tei_text = tei_root.find("{http://www.tei-c.org/ns/1.0}text")
  
  tei_body = tei_text.find("{http://www.tei-c.org/ns/1.0}body")

  ignore_tags(tei_body)
  
  tokens = extract_play_data(alto_dir)
  
  
  assert(len(tokens) > 0)

  label_funcs = [get_labels_acts, get_labels_scenes, get_labels_speakers, 
                 get_labels_stage,  get_labels_p, get_labels_stage_p, 
                 get_labels_l]

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
  for y in Y:
    assert(y != "O")

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
           "bastian-hofnarr-heidideldum", "clemens-chrischtowe", "greber-sainte-cecile", "hart-dr-poetisch-oscar", "jost-daa-im-narrehuss", "stoskopf-dr-hoflieferant", "stoskopf-ins-ropfers-apothek"]
  
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
  
    #print(choose_rand_head(n_act_heads, n_scene_heads, len(Y)))
  
    
  
  # On enlève 10 pourcent des tours de paroles d'une pièce donnée autour du 
  # début d'un acte choisi au hasard (choisi par le code ci-dessus)
  # Pour les pièces qui n'ont qu'un seul acte, on choisit une scène à la place
  acts_remove = [2, -1, -1, -1, 0, 0, 1]
  scenes_remove = [-1, -1, 9, 5, -1, -1, -1]
  random_remove = [-1, 3952, -1, -1, -1, -1, -1]
  
  return split_test_train(
                      zip(acts_remove, scenes_remove, random_remove), 
                      zip(act_heads, scene_heads), plays_XY)
  
