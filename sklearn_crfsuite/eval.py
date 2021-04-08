from acts import *

import pickle

X_train, Y_train, X_test, Y_test = get_data_sets()

crf_file = open(sys.argv[3], "rb")

crf = pickle.load(crf_file)

crf_file.close()

X = [[features_default(x, i, 0.1) for i in range(len(x))] for x in X_test]
X = [pycrfsuite.ItemSequence(x) for x in X]

pred = crf.predict(X)[0]

assert(len(pred) == len(Y_test[0]))

mistakes = 0
for y_pred, y in zip(pred, Y_test[0]):
  if y_pred != y:
    mistakes += 1

print(mistakes / len(Y_test[0]))
