#!/bin/bash
#### this script splits the content(or at least tries to) of the great os-script setup script
file="./kali.sh"
if [ -f "$file" ]
then
	echo "$file found, splitting to multiple scripts."
	csplit kali.sh '/^####/' '{*}'  
		for i in $(ls | grep xx); do mv $i $i.script;done
	for f in *.script; do d="$(head -1 $f | sed s'/#####/this script/' | sed s'/ /_/g' | awk '{print$1}').txt"; if [ ! -f "$d" ]; then mv "$f" "$d"; else echo "File '
$d' already exists! Skiped '$f'"; fi; done
	for i in *.txt; do mv $i $i.sh;done 
	more *.script > additional_scripts.txt
	rm *.script

else
	echo "$file not found, you need to run this in the os-script based folder, for more information https://github.com/g0tmi1k/os-scripts"
fi
