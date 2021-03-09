#!/bin/bash

# Nettoie les fichiers HOCR produits par tesseract afin qu'ils puissent
# être convertis en ALTO par ocr-transform
# Emploi : clean-hocr.sh <entrée> <sortie>
# Exemple : clear-hocr.sh 03.html 03-clean.html

if [ "$#" -ne 2 ]; then
  echo "Emploi : clean-hocr.sh <entrée> <sortie>"
  exit 1
fi

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

# Remplacer ocr_caption par ocr_line, pour éviter que ocr-transform génère
# des <TextBlock> sans <TextLine>
sed -i 's/ocr_caption/ocr_line/g;'     $2
