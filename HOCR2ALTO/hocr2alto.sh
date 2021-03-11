#!/bin/bash

# Convertit les fichiers HOCR produits par Tesseract en ALTO pour GROBID
# Emploi : hocr2alto.sh <entrée> <sortie>
# Exemple : hocr2alto.sh 03.html 03.xml

# Nettoie les fichiers HOCR produits par tesseract afin qu'ils puissent
# être convertis en ALTO par ocr-transform
# 2 arguments: <fichier d'entrée> <fichier de sortie>
function clean_hocr {

  # Copier l'entrée pour pouvoir modifier la sortie directement
  cp $1 $2
  
  # Supprimer les variables (inutiles ?) qui ne sont pas reconnues par 
  # ocr-transform : x_ascenders, x_descenders, x_font, x_fsize, ppageno, rot
  sed -i 's/x_ascenders [0-9\.]\+; //g'  $2
  sed -i 's/x_descenders [0-9\.]\+; //g' $2
  sed -i 's/x_font [^;]*; //g;'          $2 
  sed -i 's/ rot "/"/g'                  $2 
  sed -i 's/ ppageno ;//g'               $2 
  sed -i 's/; res [0-9]\+//g'            $2
  sed -i 's/x_font ; //g'                $2
  sed -i 's/x_fsize [^;]*; //g'          $2
  
  # Remplacer ocr_caption, ocr_textfloat, et ocr_header par ocr_line, 
  # pour éviter que ocr-transform génère des <TextBlock> sans <TextLine>
  sed -i 's/ocr_caption/ocr_line/g;'     $2
  sed -i 's/ocr_header/ocr_line/g;'      $2
  sed -i 's/ocr_textfloat/ocr_line/g;'   $2

}

if [ "$#" -ne 2 ]; then
  echo "Emploi : $0 <entrée> <sortie>"
  exit 1
fi

clean_hocr $1 $2

ocr-transform hocr alto3.0 $2 $2

xmllint --format $2 -o $2

# Insérer des valeurs factices pour les variables HEIGHT et WIDTH
# quand elles manquent
sed -i 's/HEIGHT=""/HEIGHT="1"/g' $2
sed -i 's/WIDTH=""/WIDTH="1"/g' $2

# Valider le résultat
ocr-validate alto-3-0 $2

