from lxml import etree

import re

def speaker_id(character):
  result = character.lower()

  for a, b in zip(" äöüàèìòùáéíóúâêîôû", "_aouaeiouaeiou"):
    result = result.replace(a, b)

  return re.sub('[^a-z_]', '', result)

def gen_speaker_ids(characters):
  return [speaker_id(c) for c in characters]

label_tag_map = {"scene_head" : "head", "act_head" : "head", "p" : "p", 
                 "chanson" : "l", "stage" : "stage", "speaker" : "speaker"}

def insert_all_of_same_tag(text, tokens, labels, i):
  if text == None:
    text = ""

  tag = labels[i]
  text += tokens[i]
  i += 1
  while i < len(labels) and labels[i] == tag:
    text += " " + tokens[i]
    i += 1
  return text, i

def generate_contiguous(tokens, labels, i):
  element_tag = label_tag_map[labels[i]]

  el = etree.Element(element_tag)
  el.text, i = insert_all_of_same_tag(el.text, tokens, labels, i)
  return el, i

def generate_p(tokens, labels, i):
  p = etree.Element("p")

  while i < len(labels) and (labels[i] == "chanson" or labels[i] == "p" or labels[i] == "stage"):
    if labels[i] == "p":
      if len(p) == 0:
        p.text, i = insert_all_of_same_tag(p.text, tokens, labels, i)
      else:
        p[-1].tail, i = insert_all_of_same_tag(p[-1].tail, tokens, labels, i)
    else:
      # TODO: il faut un <l> pour chaque vers (chaque ligne)
      l, i = generate_contiguous(tokens, labels, i)
      p.append(l)

  return p, i

def generate_sp(tokens, labels, i):
  sp = etree.Element("sp")

  speaker = etree.SubElement(sp, "speaker")
  speaker.text, i = insert_all_of_same_tag(speaker.text, tokens, labels, i)

  # TODO: ajouter le champs "who" à l'élément sp
  # en se basant sur la liste de personnages

  while i < len(labels) and (labels[i] == "stage" or labels[i] == "p"
        or labels[i] == "chanson"):
    if labels[i] == "p" or labels[i] == "chanson":
      p, i = generate_p(tokens, labels, i)
      sp.append(p)
    elif labels[i] == "stage":
      el, i = generate_contiguous(tokens, labels, i)
      sp.append(el)

  return sp, i

# traiter les parties de la pièce qui ne sont ni des
# act_head ni des scene_head
def process_body(parent, tokens, labels, i):
  while (i < len(labels) and labels[i] != "scene_head" 
         and labels[i] != "act_head"):
    if labels[i] == "speaker":
      sp, i = generate_sp(tokens, labels, i)
      parent.append(sp)
    else:
      el, i = generate_contiguous(tokens, labels, i)
      parent.append(el)
  return i

def generate_scene(tokens, labels, i):
  scene = etree.Element("div")
  scene.set("type", "scene")

  # <head>
  if labels[i] == "scene_head":
    head = etree.SubElement(scene, "head")
    head.text, i = insert_all_of_same_tag(head.text, tokens, labels, i)
    scene.append(head)

  i = process_body(scene, tokens, labels, i)
  return scene, i

def generate_act(tokens, labels, i):
  act = etree.Element("div")
  act.set("type", "act")
 
  # <head>
  if labels[i] == "act_head":
    head = etree.SubElement(act, "head")
    head.text, i = insert_all_of_same_tag(head.text, tokens, labels, i)
    act.append(head)

  while i < len(labels) and labels[i] != "act_head":
    if labels[i] == "scene_head":
      scene, i = generate_scene(tokens, labels, i)
      act.append(scene)
    else:
      i = process_body(act, tokens, labels, i)

  return act, i

def generate_TEI_body(tokens, labels):
  body = etree.Element("body")
  i = 0
  while i < len(tokens):
    act, i = generate_act(tokens, labels, i)
    body.append(act)

  return body
