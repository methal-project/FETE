import re

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

def features_vpos(raw_tokens, i, indent_threshold):
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
    if oa == "":
      return False
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
    'num_tokens_in_line' : line_end - line_start, 
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
      '-1word_vpos_diff' : raw_tokens[i].vpos - raw_tokens[i - 1].vpos,
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
      '+1word_vpos_diff' : raw_tokens[i+1].vpos - raw_tokens[i].vpos,
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
    features.update({'+1syl_diff' : abs(curr_line_nuc - next_line_nuc), 
        'next_line_start_vpos_diff' : raw_tokens[next_line_start].vpos - raw_tokens[i].vpos,
                         })

  if last_line_start >= 0:
    last_line_nuc = approx_nuclei(raw_tokens[last_line_start:line_start])
    features.update({'-1syl_diff' : abs(curr_line_nuc - last_line_nuc),
      'last_line_start_vpos_diff' : raw_tokens[i].vpos - raw_tokens[last_line_start].vpos,
      'last_line_start_hpos_diff' : raw_tokens[line_start].hpos - raw_tokens[last_line_start].hpos
                   })

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

  

