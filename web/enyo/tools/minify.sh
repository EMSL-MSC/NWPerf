#!/bin/bash

# the folder this script is in (*/enyo/tools)
TOOLS="$(cd `dirname $0`; pwd)"
# enyo location
ENYO="$TOOLS/.."
# minify script location
MINIFY="$TOOLS/minifier/minify.js"

# check for node, but quietly
NODE=
if command -v node >/dev/null 2>&1; then
	NODE=node
elif command -v nodejs >/dev/null 2>&1; then
	NODE=nodejs
else
	echo "No node found in path"
	exit 1
fi
# use node to invoke minify with a known path to enyo and imported parameters
$NODE "$MINIFY" -enyo "$ENYO" $@
