#!/bin/bash
set -o pipefail
SCRIPTPATH=$(dirname $0)
BASE=$1
URLPATH=$2
PATTERN=$3
DEBUG=$4
if ! which hxwls > /dev/null;then
	exit 1
fi
#hxwls sometimes reports syntaxerrors, ignore it's error codes
wget --quiet -O - "$BASE/$URLPATH" | (hxwls -b "$BASE" 2>&1 || true) | \
egrep "$PATTERN" | sed -e 's#/static/#/static-files/#' | 
while read -r line; do
  [[ "$line" != *.html ]] && line+='.html'
  if [ ! -z $DEBUG ]; then echo "DBG: $line"; fi
  output=$($SCRIPTPATH/check_url_status -o -U $line) || {
	echo "$output"
	exit 1
  }
done
