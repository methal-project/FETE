output=$(python corrections.py $1 $2)

FILENAME=`echo $output | sed 's/.*Filename: \([^ ]\+\).*/\1/g'`
ID=`echo $output | sed 's/.*id: \([^ ]\+\).*/\1/g'`
TOKEN=`echo $output | sed 's/.*TOKEN: \([^ ]\+\).*/\1/g'`
CONTEXT=`echo $output | sed 's/.*CONTEXT: \([^%]\+\).*/\1/g'`
REPLACE=`echo $output | sed 's/.*\(REPLACE: [^%]\+\).*/\1/g'`
WITH=`echo $output | sed 's/.*\(WITH: [^%]\+\).*/\1/g'`
LINENUMBER=`echo $output | sed 's/^.*LINENUMBER: \(.*\)$/\1/g'`

echo $FILENAME $ID $TOKEN

#vim -O ./html/$NAME/$FILENAME ../../methal-sources/$NAME.xml -c "/$ID" -c ":set hlsearch | :wincmd w" -c "/$CONTEXT" -c ":wincmd w"
vim -O $1/$FILENAME $2 -c "/$ID" -c ":set hlsearch | :wincmd w" -c ":$LINENUMBER" -c ":set cursorline" -c ":wincmd w"

#TOKEN=`python train.py ./html/ ../../methal-sources/ | grep TOKEN | sed 's/TOKEN: //g' `
#echo $TOKEN
#FILE=`echo $TOKEN | xargs -I XX grep XX ./html/charlot/*.html | sed 's/:.*//g'`
#echo $FILE
#vim -O $FILE ../../methal-sources/charlot.xml -c "/$TOKEN | windcmd w | /$TOKEN"
#python train.py ./html/ ../../methal-sources/ | grep TOKEN | sed 's/TOKEN: //g' | xargs -I XX grep XX ./html/charlot/*.html | sed 's/:.*//g' | xargs -o -I XX vim -O XX ../../methal-sources/charlot.xml
