from acts import *

import pickle

def train():
  X_train, Y_train, X_test, Y_test = get_data_sets()

  X_train = [[features_vpos(x, i) for i in range(len(x))] for x in X_train]
  X_train = [pycrfsuite.ItemSequence(x) for x in X_train]

  crf = sklearn_crfsuite.CRF(
              algorithm='lbfgs',
              max_iterations=1000,
              all_possible_transitions=True,
              c1=0.7,
              c2=0.0,
  )

  crf.fit(X_train, Y_train)
  return crf

crf = train()

f = open(sys.argv[3], "wb")

pickle.dump(crf, f)

f.close()
