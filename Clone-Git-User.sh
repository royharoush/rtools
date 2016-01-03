#!/bin/bash
#modified version of https://github.com/m42e/github-coup
# this version accepts username from command line
export SHELL=$(type -P bash)
targetdir="/var/github/$1"
user="$1"
token=ACCESSTOKEN
urls="/users/$user/repos /users/$user/starred"
# actions
# all actions get the following parameter
# $repo $repodir $repobasename $username
# define an action after cloning
actionafterclone(){
        # e.g. git remote add myserver xxxx.xx:github/$3  2>&1 > /dev/null
        return 
}
# define an action before fetching
actiononold(){
        return  
}
# define an action after fetching
actiononnew(){
        # e.g. git push myserver --all 2&>1 > /dev/null
        return 
}
cloneorupdate(){
        repo=$1
        #check for valid repo
        if [ `echo $repo | grep -q -e '[a-z0-9A-Z\.-\_]*/[a-z0-9A-Z\.-\_]*'` ];
        then 
                return
        fi
        echo +++++++++++++++++++++++++++++++++++++++
        echo check $repo
        repo=(`echo $repo | tr '"' ' '`)
        bar=(`echo $repo | tr '/"' '  '`)
        repobasename=${bar[1]}   
        username=${bar[0]}   
        repodir="$targetdir/$repobasename"
        if [ -d $repodir ]; then
                echo update $repo
                pushd $repodir > /dev/null
                actiononold $repo $repodir $repobasename $username
                git remote add $username https://github.com/$username/$repobasename  2&>1 > /dev/null
                actiononnew $repo $repodir $repobasename $username
                popd > /dev/null
        else
                echo clone $repo into $targetdir
                git clone https://github.com/$repo $repodir > /dev/null
                pushd $repodir > /dev/null
                actionafterclone $repo $repodir $repobasename $username
                actiononnew $repo $repodir $repobasename $username
                popd > /dev/null
        fi
        echo done $repo
        echo --------------------------------------
}
# necessary exports 
export targetdir
export -f cloneorupdate
export -f actiononnew
export -f actiononold
export -f actionafterclone
abs=0
curltoken=
if [ "$token" != "" ]; then
        curltoken=" -H \"Authorization: token $token\""
fi
for url in $urls
do
        found=1
        nr=1
        link="https://api.github.com$url?page=1&per_page=1000"
        headerfile=/tmp/curlheaders.$RANDOM.$RANDOM.$RANDOM.$$
        while [ "$link" != "" ]; do
                echo Fetching repositories, $link
                data=`curl --silent -D $headerfile $curltoken $link`
                if [ $? -ne 0 ]; then
                        echo curl failed fetching $link
                        break;
                fi
                # print message and break if github has something to tell
                has_message=`echo $data | jq "if . | objects then has(\"message\") else false end"`
                if [ "$has_message" == "true" ]; then
                        message=`echo $data | jq ".message"`
                        if [ "$message" != "" ]; then
                                echo request failed $message
                                break;
                        fi
                fi
                repos=`echo $data | jq ".[].full_name"`
                count=`echo $repos | wc -w`
                if [ $count -eq 0 ]; then
                        break
                fi
                abs=$((abs + $count))
                # get the repos, use parallel if available
                if $(hash parallel 2>/dev/null); then
                        SHELL=$(type -P bash) parallel --gnu -j 20 cloneorupdate ::: $repos
                else
                        for repo in $repos
                        do
                                cloneorupdate $repo
                        done
                fi
                link=`cat $headerfile | grep -o -e '<[^>]*>; rel="next"' | sed -e 's/<\([^>]*\)>.*/\1/'`
                rm $headerfile
        done
done
echo checked $abs repositories
