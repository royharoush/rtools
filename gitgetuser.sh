#!/bin/bash
if [ "$#" -ne 2 ]; then
    echo "Please provide a git username and whether you want to see repos or starred"
    echo "exmaple: gitgetuser.sh royharoush starred\repos"
	else 
	echo "Getting the $2 for $1"
	for page in 1 2 3 4 ; do curl "https://api.github.com/users/$1/$2?page=$page&per_page=99" | grep  'name\|"description\|clone_url' | sed s'\,\\' | sed "/\b\(labels_url\|full_name\)\b/d"  |tr -d '"' |  sed s'jname:j##############j' | sed s'kdescription:k###k'| sed s'sclone_url:sgit clones'   | awk '$1=="##############"{x=$0;next} $1=="###"{print x, $0; next} 1' | sed  's/^ *//' ;done >$1-$2.txt
	cat $1-$2   | paste - -    | sed 's/############## //g' | sed 's\     ### \,\g' | sed 's\git clone \, git clone \g' > $1-$2.csv


fi
