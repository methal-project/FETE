from acts import *

import pickle

crf_file = open(sys.argv[1], "rb")

crf = pickle.load(crf_file)

crf_file.close()

tokens = [extract_play_data(sys.argv[2])]

#personnages = []
#
#if len(sys.argv) > 4:
#  char_list_file = open(sys.argv[4], "r")
#
#  personnages = [x.lower().split() for x in char_list_file.readlines()]
#
#  print(personnages)
#
#for i, t in enumerate(tokens[0]):
#  if (sum([only_alpha(t.string).lower() in p for p in personnages])
#      and (t.is_line_start or tokens[0][i-1].is_line_start or tokens[0][i-2].is_line_start)):
#    #print(t.string, t.string.replace(".", ":"))
#    tokens[0][i].string = t.string.replace(".", ":")

X = [[features_vpos(x, i, 0.3) for i in range(len(x))] for x in tokens]
X = [pycrfsuite.ItemSequence(x) for x in X]

pred = crf.predict(X)[0]

tei_generator = TEIGen([x.string for x in tokens[0]], pred, ["doctor"], [x.page_num for x in tokens[0]], 5, [x.is_line_start for x in tokens[0]])

tei = tei_generator.generate_TEI_body()

f = open(sys.argv[3], "wb")

etree.ElementTree(tei).write(f, encoding='UTF-8')

f.close()

