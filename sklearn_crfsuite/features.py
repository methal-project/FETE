import re

def only_alpha(word):
  return re.sub('[^A-Za-zè]', '', word)

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
  if oa == "":
    return False
  for c in oa:
    result = result and c in 'ivx'
  return result

def find_line_start(raw_tokens, i):
  while i >= 0:
    if raw_tokens[i].is_line_start:
      return i
    i -= 1
  return i

def find_line_end(raw_tokens, i):
  while i < len(raw_tokens) - 1:
    if raw_tokens[i + 1].is_line_start:
      return i
    i += 1
  return i

def find_line_boundaries(raw_tokens, i):
  line_end = find_line_end(raw_tokens, i)

  next_line_end = find_line_end(raw_tokens, line_end + 1)

  line_start = find_line_start(raw_tokens, i)

  last_line_start = find_line_start(raw_tokens, i - 1)

  return last_line_start, line_start, line_end, next_line_end

INCREASE = "INCREASE"
CONSTANT = "CONSTANT"
DECREASE = "DECREASE"
def threshold_compare(a, b, thresh):
  result = CONSTANT
  if a - b > thresh:
    result = INCREASE
  elif a - b < -thresh:
    result = DECREASE
  return result

def prefix_map(prefix, m):
  result = {}
  for k in m:
    result[prefix + k] = m[k]
  return result

def token_features(token):
  word = token.string

  features = {
    'word': word,
    'line_start': token.is_line_start,
    'word.lower()': word.lower(),
    'word[0].isupper()': word[0].isupper(),
    'word_contains_period' : '.' in word,
    'word_contains_colon' : ':' in word,
    'word_contains_lparen' : '(' in word,
    'word_contains_rparen' : ')' in word, 
    'word_contains_digit' : bool(re.search('[0-9]', word)),
    'word_is_acty' : is_acty(word),
    'word_is_sceney' : is_sceney(word),
    'word_rom_num' : is_rom_num(word),
    'hpos' : token.hpos,
    'fsize_norm' : token.fsize,
  }

  return features

def token_features_context(raw_tokens, i):
  features = token_features(raw_tokens[i])
  if i > 0:
    features_last_word = token_features(raw_tokens[i-1])
    features.update(prefix_map("-1", features_last_word))
 
  if i < len(raw_tokens) - 1:
    features_next_word = token_features(raw_tokens[i+1])
    features.update(prefix_map("+1", features_next_word))

  return features

def line_features(raw_tokens, i):
  last_line_start, line_start, line_end, next_line_end = find_line_boundaries(
                                                                 raw_tokens, i)
  features = {
    'line_end_hpos' : raw_tokens[line_end].hpos,
    'num_tokens_in_line' : line_end - line_start, 
  }
  return features

def inter_token_features(raw_tokens, i):
  fsize = CONSTANT
  if i > 0:
    fsize = threshold_compare(raw_tokens[i].fsize, raw_tokens[i-1].fsize, 0.0)
  return {"fsize" : fsize}

def inter_line_features(raw_tokens, i):
  result = {}

  last_line_start, line_start, line_end, next_line_end = find_line_boundaries(
                                                                 raw_tokens, i)

  line_start_hpos = raw_tokens[line_start].hpos

  if last_line_start >= 0:
    result.update({
      'last_line_start_vpos_diff' : raw_tokens[line_start].vpos - raw_tokens[last_line_start].vpos,
      'last_line_start_hpos_diff' : raw_tokens[line_start].hpos - raw_tokens[last_line_start].hpos,
                })

  next_line_start = line_end + 1
  if next_line_start < len(raw_tokens):
    result.update({
      'next_line_start_vpos_diff' : raw_tokens[line_start].vpos - raw_tokens[next_line_start].vpos,
      'next_line_start_hpos_diff' : raw_tokens[line_start].hpos - raw_tokens[next_line_start].hpos,
                })

  return result

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

def rhyme_features(tok1, tok2):
  word1 = re.sub('[!"\,\.\?]', '', tok1.string)
  word2 = re.sub('[!"\,\.\?]', '', tok2.string)
  features = {}
  if len(word1) > 0 and len(word2) > 0:
    features.update({
                 "rhyme_1" : word1[-1] == word2[-1],
                 "rhyme_2" : word1[-2:] == word2[-2:],
                 "rhyme_3" : word1[-3:] == word2[-3:],
               })
  return features

# Caractéristiques conçues pour détecter les vers
def vers_features(raw_tokens, i):
  last_line_start, line_start, line_end, next_line_end = find_line_boundaries(
                                                                 raw_tokens, i)

  last_line_end = line_start - 1

  features = {}

  next_line_start = line_end + 1
  curr_line_nuc = approx_nuclei(raw_tokens[line_start:next_line_start])

  if next_line_end < len(raw_tokens):
    tok1 = raw_tokens[line_end]
    tok2 = raw_tokens[next_line_end]
    features.update(prefix_map("+1", rhyme_features(tok1, tok2)))

    next_line_nuc = approx_nuclei(raw_tokens[next_line_start:next_line_end + 1])
    features.update({'+1syl_diff' : abs(curr_line_nuc - next_line_nuc)})


  if last_line_end >= 0:
    tok1 = raw_tokens[line_end]
    tok2 = raw_tokens[last_line_end]
    features.update(prefix_map("-1", rhyme_features(tok1, tok2)))
    
    last_line_nuc = approx_nuclei(raw_tokens[last_line_start:last_line_end + 1])
    features.update({'-1syl_diff' : abs(curr_line_nuc - last_line_nuc)})

  return features
    

def features_vpos(raw_tokens, i):
  word = raw_tokens[i].string

  features = {}

  features.update(token_features_context(raw_tokens, i))
  features.update(inter_token_features(raw_tokens, i))

  features.update(line_features(raw_tokens, i))
  features.update(inter_line_features(raw_tokens, i))

  features.update(vers_features(raw_tokens, i))

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

  

