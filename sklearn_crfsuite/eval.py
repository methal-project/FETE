from acts import *

from zss import simple_distance, Node

import pickle

def xml_to_zss(xml, zss_root):
  node_label = xml.tag

  # Distinguish acts from scenes
  if node_label == "div": 
    node_label += xml.get("type")

  this_zss = Node(node_label)

  for c in xml:
    xml_to_zss(c, this_zss)

  zss_root.addkid(this_zss)
  return zss_root

X_train, Y_train, X_test, Y_test = get_data_sets()

crf_file = open(sys.argv[3], "rb")

crf = pickle.load(crf_file)

crf_file.close()

X = [features_set_3_glob(x) for x in X_test]
X = [pycrfsuite.ItemSequence(x) for x in X]

pred = crf.predict(X)

tag_map = {}

for Y in Y_train:
  for y in Y:
    if y not in tag_map:
      tag_map[y] = 0
    tag_map[y] += 1

for k in tag_map:
  print(k, tag_map[k])

print("total", sum([len(y) for y in Y_train]) + sum([len(y) for y in Y_test]))

"""
for i, (pred_seq, true_seq) in enumerate(zip(pred, Y_test)):
  pred_gen = TEIGen([x.string for x in X_test[i]], pred_seq, ["doctor"], [x.page_num for x in X_test[i]], 5, [x.is_line_start for x in X_test[i]])
  true_gen = TEIGen([x.string for x in X_test[i]], true_seq, ["doctor"], [x.page_num for x in X_test[i]], 5, [x.is_line_start for x in X_test[i]])
  true_tei = true_gen.generate_TEI_body()
  pred_tei = pred_gen.generate_TEI_body()

  true_zss = xml_to_zss(true_tei, Node("Dummy"))
  pred_zss = xml_to_zss(pred_tei, Node("Dummy"))

  print(simple_distance(true_zss, pred_zss))
"""

print(metrics.flat_classification_report(
  Y_test, pred, digits=3
))

