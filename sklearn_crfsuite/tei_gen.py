from lxml import etree

import re

import Levenshtein

def speaker_id(character):
  result = character.lower()

  for a, b in zip(" äöüàèìòùáéíóúâêîôû", "_aouaeiouaeiou"):
    result = result.replace(a, b)

  return re.sub('[^a-z_]', '', result)

def gen_speaker_ids(characters):
  return [speaker_id(c) for c in characters]


class TEIGen:

  def __init__(self, tokens, labels, characters):
    self.tokens = tokens
    self.labels = labels

    self.sid_map = {}
    for c in characters:
      self.sid_map[c] = speaker_id(c)

    self.label_tag_map = {"scene_head" : "head", "act_head" : "head", "p" : "p", 
                 "chanson" : "l", "stage" : "stage", "speaker" : "speaker"}

  def find_speaker_id(self, speaker):
    #min_dist = 100000
    #best_id = ""
    #for c in self.sid_map:
    #  dist = Levenshtein.distance(c, speaker)
    #  if dist < min_dist:
    #    min_dist = dist
    #    best_id = c
    #return best_id
    for c in self.sid_map:
      if speaker.replace(":", "") in c:
        return self.sid_map[c]

    return "UNKNOWN"

  def insert_all_of_same_tag(self, text):
    if text is None:
      text = ""
  
    tag = self.labels[self.i]
    text += self.tokens[self.i]
    self.i += 1
    while self.i < len(self.labels) and self.labels[self.i] == tag:
      text += " " + self.tokens[self.i]
      self.i += 1

    return text
  
  def generate_contiguous(self):
    element_tag = self.label_tag_map[self.labels[self.i]]
  
    el = etree.Element(element_tag)
    el.text = self.insert_all_of_same_tag(el.text)
    return el
  
  def generate_p(self):
    p = etree.Element("p")
  
    while self.i < len(self.labels) and (self.labels[self.i] == "chanson" 
                                    or self.labels[self.i] == "p" 
                                    or self.labels[self.i] == "stage"):
      if self.labels[self.i] == "p":
        if len(p) == 0:
          p.text = self.insert_all_of_same_tag(p.text)
        else:
          p[-1].tail = self.insert_all_of_same_tag(p[-1].tail)
      else:
        # TODO: il faut un <l> pour chaque vers (chaque ligne)
        l = self.generate_contiguous()
        p.append(l)
  
    return p
  
  def generate_sp(self):
    sp = etree.Element("sp")
  
    speaker = etree.SubElement(sp, "speaker")
    speaker.text = self.insert_all_of_same_tag(speaker.text) 

    sp.set("who", self.find_speaker_id(speaker.text))
  
    while self.i < len(self.labels) and (self.labels[self.i] == "stage" 
                                         or self.labels[self.i] == "p"
                                         or self.labels[self.i] == "chanson"):
      if self.labels[self.i] == "p" or self.labels[self.i] == "chanson":
        p = self.generate_p()
        sp.append(p)
      elif self.labels[self.i] == "stage":
        el = self.generate_contiguous()
        sp.append(el)
  
    return sp
  
  # traiter les parties de la pièce qui ne sont ni des
  # act_head ni des scene_head
  def process_body(self, parent):
    while (self.i < len(self.labels) and self.labels[self.i] != "scene_head" 
           and self.labels[self.i] != "act_head"):
      if self.labels[self.i] == "speaker":
        sp = self.generate_sp()
        parent.append(sp)
      else:
        el = self.generate_contiguous()
        parent.append(el)
  
  def generate_scene(self):
    scene = etree.Element("div")
    scene.set("type", "scene")
  
    # <head>
    if self.labels[self.i] == "scene_head":
      head = etree.SubElement(scene, "head")
      head.text = self.insert_all_of_same_tag(head.text)
  
    self.process_body(scene)
    return scene
  
  def generate_act(self):
    act = etree.Element("div")
    act.set("type", "act")
   
    # <head>
    if self.labels[self.i] == "act_head":
      head = etree.SubElement(act, "head")
      head.text = self.insert_all_of_same_tag(head.text)
  
    while self.i < len(self.labels) and self.labels[self.i] != "act_head":
      if self.labels[self.i] == "scene_head":
        scene = self.generate_scene()
        act.append(scene)
      else:
        self.process_body(act)
  
    return act
  
  def generate_TEI_body(self):
    body = etree.Element("body")
    self.i = 0
    while self.i < len(self.tokens):
      act = self.generate_act()
      body.append(act)
  
    return body
