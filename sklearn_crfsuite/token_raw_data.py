class TokenRawData:
  def __init__(self, string, hpos, fsize, is_line_start, line_start_hpos,  
               word_id, vpos):
    self.string = string
    self.hpos = hpos
    self.fsize = fsize
    self.is_line_start = is_line_start
    self.line_start_hpos = line_start_hpos
    self.page_num = -1
    self.filename = ""
    self.word_id = word_id
    self.vpos = vpos

  def __str__(self):
    return ("('" + self.string + "', " + str(self.hpos) + ", " + 
                                          str(self.fsize) + ")") # TODO
 
  def __repr__(self):
    return str(self)
