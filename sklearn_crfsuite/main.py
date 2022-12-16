from acts import *

import html
import pickle

crf_file = open(sys.argv[1], "rb")

(feature_function, crf) = pickle.load(crf_file)

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

X = [feature_function(x) for x in tokens]
X = [pycrfsuite.ItemSequence(x) for x in X]

pred = crf.predict(X)[0]

tei_generator = TEIGen([x.string for x in tokens[0]], pred, ["doctor"], [x.page_num for x in tokens[0]], 5, [x.is_line_start for x in tokens[0]])

tei = tei_generator.generate_TEI_body()

f = open(sys.argv[3], "wb")

etree.ElementTree(tei).write(f, encoding='UTF-8')

f.close()

# indent XML and add CSS
formatted_name = os.path.splitext(sys.argv[3])[0] + "_f.xml"
formatted_unescaped = os.path.splitext(formatted_name)[0] + "_fu.xml"
os.system(f"xmllint --format {sys.argv[3]} > {formatted_name}")

TEI_HEADER = """<teiHeader>
  <fileDesc>
    <titleStmt>
      <title></title>
    </titleStmt>
    <publicationStmt>
      <publisher></publisher>
    </publicationStmt>
    <sourceDesc>
      <bibl></bibl>
    </sourceDesc>
  </fileDesc>
</teiHeader>"""

with open(formatted_name, mode="r", encoding="utf-8") as ixml,\
    open(formatted_unescaped, mode="w", encoding="utf-8") as oxml:
    txt = ixml.read()
    # need a TEI root for CSS to add margins
    oxml.write(html.unescape(txt).replace('<?xml version="1.0"?>',
                                          """<?xml version="1.0"?>\n""" 
                                          """<?xml-stylesheet type='text/css' href='../../../css/tei-drama.css' ?>\n""" +
                                          """<TEI xmlns="http://www.tei-c.org/ns/1.0">\n{}\n<text>""".format(
                                           TEI_HEADER)).replace("</body>", "</body>\n</text>\n</TEI>"))

os.system(f"mv {formatted_unescaped} {sys.argv[3]}")
os.system(f"rm {formatted_name}")

