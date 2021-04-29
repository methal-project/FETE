from token_raw_data import *

from process_common import *

import re

def extract_raw_data_html(node, font_size=0.0, 
                          is_line_start=False, line_start_hpos=0.0):
  result = []
  if node.tag == "span":
    cl = node.get("class")
    if cl == "ocr_line":
      title = node.get("title")
      title = title.replace(";", "").split()
      idx = title.index("x_size")
      font_size = float(title[idx + 1])
      is_line_start = True
    elif cl == "ocrx_word":
      if node.text is not None:
        content = finaggle(node.text)
        if content.isspace() or content == '':
          return []
        title = node.get("title")
        title = title.replace(";", "").split()
        bbox = title.index("bbox")
        hpos = int(title[bbox + 1])
        content = re.sub("-[0-9]+-", "", content)
        n_token = TokenRawData(content, hpos, font_size, is_line_start, 
                               line_start_hpos, node.get("id"))
        result.append(n_token)
  
  for c in node:
    result += extract_raw_data_html(c, font_size=font_size, 
                                    is_line_start=is_line_start,
                                    line_start_hpos=line_start_hpos)
    if len(result) > 0:
      if is_line_start:
        line_start_hpos = result[-1].hpos
        result[-1].line_start_hpos = result[-1].hpos
    is_line_start = False

  return result

def remove_page_number_html(node):
  for c in node:
    if ((c.tag == "span" and c.get("class") in ["ocr_line",  "ocr_caption", "ocr_header", "ocr_textfloat", "ocr_par"])
        or (c.tag == "p" and c.get("class") == "ocr_par" and 
            sum([len(p) for p in c]) == 0)):
      result = ""
      for string in c:
        if string.text is not None:
          result += string.text


      if result.isspace() or result == "":
        continue

      if not bool(re.search('[A-Za-z]', result)):
        #print(result)
        # Supprimer
        for string in c:
          string.text = ""
        return True
    else:
      if remove_page_number_html(c):
        return True

  return False
