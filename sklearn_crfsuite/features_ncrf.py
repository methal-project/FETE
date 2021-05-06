from acts import *
from features import *

X_train, Y_train, X_test, Y_test = get_data_sets()

X_tv = X_train

Y_tv = Y_train

act_heads = [find_act_heads(Y) for Y in Y_tv]
scene_heads = [find_scene_heads(Y) for Y in Y_tv]

X_train, Y_train, X_valid, Y_valid = split_test_train(
                                    [choose_rand_head(a, s, l) for a, s, l in zip(
                                     act_heads, scene_heads, [len(y) for y in Y_tv])],
                                     zip(act_heads, scene_heads), zip(X_tv, Y_tv))

def write_token(f, x, y, prefix, features):
  x.string = x.string.replace("\n", "").replace("\t", "")
  last_line_start_vpos_diff = 0.0
  last_line_start_hpos_diff = 0.0
  last_line_syl_diff = -1
  last_rhyme_1 = False
  last_rhyme_2 = False
  last_rhyme_3 = False
  if 'last_line_start_vpos_diff' in features:
    last_line_start_vpos_diff = features['last_line_start_vpos_diff']
    last_line_start_hpos_diff = features['last_line_start_hpos_diff']
    last_line_syl_diff = features['-1syl_diff']
  if '-1rhyme_1' in features:
    last_rhyme_1 = features['-1rhyme_1']
    last_rhyme_2 = features['-1rhyme_2']
    last_rhyme_3 = features['-1rhyme_3']
  f.write(x.string + " " 
          + "[HPOS]" + str(round(last_line_start_hpos_diff, 1)) + " "
          + "[VPOS]" + str(round(last_line_start_vpos_diff, 2)) + " "
          + "[LPAREN]" + str("(" in x.string) + " "
          + "[RPAREN]" + str(")" in x.string) + " "
          + "[LINESTART]" + str(x.is_line_start) + " "
          + "[FSIZE]" + str(round(x.fsize, 1)) + " "
          + "[SCENEY]" + str(features['word_is_sceney']) + " "
          + "[ACTY]" + str(features['word_is_acty']) + " "
          + "[DIGIT]" + str(features['word_contains_digit']) + " "
          + "[ROMNUM]" + str(features['word_rom_num']) + " "
          + "[SYLDIFF]" + str(last_line_syl_diff) + " " 
          + "[RHYME1]" + str(last_rhyme_1) + " "
          + "[RHYME2]" + str(last_rhyme_2) + " "
          + "[RHYME3]" + str(last_rhyme_3) + " "
          + "[ENDHPOS]" + str(round(features['line_end_hpos'], 1)) + " "
          + "[LINETOKS]" + str(features['num_tokens_in_line']) + " "
          + prefix + y + "\n")

def write_file(f, X_set, Y_set):
  for X, Y in zip(X_set, Y_set):
    last_tag = ""
    for i, (x, y) in enumerate(zip(X, Y)):
      prefix = "B-"
      #if i == len(X) - 1 or y != Y[i+1]:
      #  if i > 0 and y == Y[i - 1]:
      #    prefix = "E-"
      #  else:
      #    prefix = "S-"
      #elif y != last_tag:
      #  prefix = "B-"
      #else:
      #  prefix = "M-"
      
      if " " in x.string:
        for s in x.string.split():
          write_token(f, x, y, prefix, features_vpos(X, i, 0.1))
      else:
        write_token(f, x, y, prefix, features_vpos(X, i, 0.1))
      last_tag = y
    f.write("\n")

train_f = open("train.bmes", "w")

write_file(train_f, X_train, Y_train)

train_f.close()

valid_f = open("dev.bmes", "w")

write_file(valid_f, X_valid, Y_valid)

valid_f.close()
