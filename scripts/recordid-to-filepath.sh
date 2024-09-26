#!/bin/bash

# This script returns the exact path of a record.
# Pass the id as the first argument.
# On finding the correct file, it prints its path to the console.

if [ $# -eq 0 ]; then
  echo "Error: No record ID provided."
  exit 1
fi

result=$(
  grep -ri "$1" /content/data/records/ |
  grep  '"recid"' |
  awk -F':' '{print $0, match($2, /^[ \t]*/)}' |
  sort -k2,2n |
  head -n1 |
  cut -d':' -f1
);
echo "${result:-No file found with record id \`$1\`}"
