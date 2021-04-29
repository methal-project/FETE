def finaggle(s):
  return s.replace("‘", "'").replace("’", "'").replace("}", ")").replace("“","\"").replace("—","-").replace("”", "\"").replace("―", "-").replace("„", "\"").replace("…", "...").replace("=", "-").replace("{", "(").replace(",,", "\"")

# Ignorer les éléments seg, emph et span
def ignore_tags(root):
  removals = set()
  for child in root:
    ignore_tags(child)
  for i in range(len(root) - 1, -1, -1):
    #print(i, root[i].tag)
    if (root[i].tag == "{http://www.tei-c.org/ns/1.0}emph" 
       or root[i].tag == "{http://www.tei-c.org/ns/1.0}seg"
       or root[i].tag == "{http://www.tei-c.org/ns/1.0}span"
       or root[i].tag == "strong" or root[i].tag == "em"
       or root[i].tag == "{http://www.tei-c.org/ns/1.0}quote" 
       or root[i].tag == "{http://www.tei-c.org/ns/1.0}note"):

      if i > 0:
        if root[i-1].tail is None:
          root[i-1].tail = ""
        if root[i].text is not None:
          root[i-1].tail += root[i].text
        if root[i].tail is not None:
          root[i-1].tail += root[i].tail
      else:
        if root.text is None:
          root.text = ""
        if root[i].text is not None:
          root.text += root[i].text
        if root[i].tail is not None:
          root.text += root[i].tail
      removals.add(root[i])

  for r in removals:
    root.remove(r)
