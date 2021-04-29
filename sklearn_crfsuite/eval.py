from acts import *

import pickle

X_train, Y_train, X_test, Y_test = get_data_sets()

crf_file = open(sys.argv[3], "rb")

crf = pickle.load(crf_file)

crf_file.close()

X = [[features_syl(x, i, 0.1) for i in range(len(x))] for x in X_test]
X = [pycrfsuite.ItemSequence(x) for x in X]

pred = crf.predict(X)

print(metrics.flat_classification_report(
  Y_test, pred, digits=3
))

