from acts import *

import pickle

crf_file = open(sys.argv[1], "rb")

crf = pickle.load(crf_file)

crf_file.close()

tokens = [extract_play_data(sys.argv[2])]

X = [[features_syl(x, i, 0.3) for i in range(len(x))] for x in tokens]
X = [pycrfsuite.ItemSequence(x) for x in X]

pred = crf.predict(X)[0]

tei_generator = TEIGen([x.string for x in tokens[0]], pred, ["doctor"], [x.page_num for x in tokens[0]], 5, [x.is_line_start for x in tokens[0]])

tei = tei_generator.generate_TEI_body()

f = open(sys.argv[3], "wb")

etree.ElementTree(tei).write(f, encoding='UTF-8')

f.close()

