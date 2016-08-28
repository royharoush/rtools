#!/bin/bash
echo    "########## Downloading GNX and gnmap-parser tools to this directory ############"
wget https://raw.githubusercontent.com/royharoush/rtools/master/gnxmerge.py &> /dev/null
wget https://raw.githubusercontent.com/royharoush/rtools/master/gnxparse.py &> /dev/null
wget https://raw.githubusercontent.com/royharoush/rtools/master/gnmap-parser.sh &> /dev/null
now=$(date +"%d-%m-%y"-"%T" |tr ":" "-" | cut -d"-" -f1,2,3,4,5)
mkdir Results-$now
echo    "########## Download Complete ############"
echo    "########## GNX Nmap Tools Are Now Inside Your Directory ############"
echo    "########## Modified Gnmap-Parser is now Inside Your Directory ############"
echo ##### This can be used to remove files that don't have any open ports 
echo #find -name '*.xml'   | xargs -I{} grep -LZ "state=\"open\"" {} | while IFS= read -rd '' x; do mv "$x" "$x".empty ; done 
echo #find -name '*.xml' -exec grep -LZ "state=\"open\"" {} + |  perl -n0e 'rename("$_", "$_.empty")'
echo "I will now parse all your XMLs into one file called gnx-merged-$now.xml" 
python gnxmerge.py -s ./  > gnx-merged-$now.xml
echo "I will now create the outputs of your scans from the XML file" 
python gnxparse.py Results-$now/gnx-merged-$now.xml -i -p -s -r -c >c> gnx-output_all-$now.csv 
python gnxparse.py Results-$now/gnx-merged-$now.xml -p >> gnx-Open-Ports.txt 
python gnxparse.py Results-$now/gnx-merged-$now.xml -i >> gnx-Live-IPs.txt
python gnxparse.py Results-$now/gnx-merged-$now.xml -s >> gnx-Subnets.txt
python gnxparse.py Results-$now/gnx-merged-$now.xml -c >> gnx-Host-Ports-Matrix.csv  
python gnxparse.py Results-$now/gnx-merged-$now.xml -r 'nmap -A ' >> ./gnx-suggested_scans-$now.sh
echo "########All Done, Merged XML is in gnx-merged-$now.xml########"
echo "########Scan data can be found in gnx* files########" 
echo "############parsing Gnmap files##########"
find . -maxdepth 1 -type f -name '*.gnmap' -print0 |  sort -z |  xargs -0 cat -- >> ./Results-$now/gnmap-merged.gnmap
echo "############parsing Gnmap files##########"
bash ./gnmap-parser.sh -p
mv Parsed-Results/ ./Results-$now/
mv ./gnmap-parser.sh ./Results-$now/
mv gnx* ./Results-$now/
cat ./Results-$now/Parsed-Results/Host-Lists/Alive-Hosts-Open-Ports.txt > ./Results-$now/Gnmap-LiveHosts.txt
cat ./Results-$now/Parsed-Results/Port-Lists/TCP-Ports-List.txt  | tr "\n" "," > ./Results-$now/Gnmap-OpenPorts.txt
echo "#### Downloading nmapParse.sh####"
echo "Comperessing current run's Nmap output and removing files"
tar -cvzf NmapFiles-$now.tar.gz --remove-files *.nmap
tar -cvzf XMLFiles-$now.tar.gz --remove-files *.xml
tar -cvzf GnmapFiles-$now.tar.gz --remove-files *.gnmap
mv *.tar.gz ./Results-$now/
ls Results-$now -latr | tail -n 10
echo "Have fun !"
