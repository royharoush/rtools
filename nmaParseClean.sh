#!/bin/bash
echo    "########## Downloading GNX and gnmap-parser tools to this directory ############"
wget https://raw.githubusercontent.com/royharoush/rtools/master/gnxmerge.py -O gnxmerge.py&> /dev/null
wget https://raw.githubusercontent.com/royharoush/rtools/master/gnxparse.py -O gnxparse.py &> /dev/null
wget https://raw.githubusercontent.com/royharoush/rtools/master/gnmap-parser.sh -O gnmap-parser.sh &> /dev/null
wget https://raw.githubusercontent.com/royharoush/rtools/master/nmap2csv.py -O nmap2csv.py &> /dev/null
now=$(date +"%d-%m-%y"-"%T" |tr ":" "-" | cut -d"-" -f1,2,3,4,5)
mkdir Results-$now
echo    "########## Download Complete ############"
echo    "########## GNX Nmap Tools Are Now Inside Your Directory ############"
echo    "########## Modified Gnmap-Parser is now Inside Your Directory ############"
echo ##### This can be used to remove files that don't have any open ports 
echo #find -name '*.xml'   | xargs -I{} grep -LZ "state=\"open\"" {} | while IFS= read -rd '' x; do mv "$x" "$x".empty ; done 
echo #find -name '*.xml' -exec grep -LZ "state=\"open\"" {} + |  perl -n0e 'rename("$_", "$_.empty")'
echo "Generating SQLite Database from only the XML files that contain live hosts" 
wget https://raw.githubusercontent.com/royharoush/rtools/master/nmapdb.py -O nmapdb.py &> /dev/null
wget https://raw.githubusercontent.com/argp/nmapdb/master/nmapdb.sql -O nmapdb.sql &> /dev/null
grep -r  --include \*.xml "state=\"open\""   | cut -d":" -f1 | sort -u  > livexml.manifest
mkdir livexmlforsqlite
for i in $(cat livexml.manifest); do cp $i ./livexmlforsqlite/;done
rsync -v  --files-from=livexml.manifest ./  ./livexmlforsqlite/
find ./livexmlforsqlite/ -name '*.xml'  -exec python nmapdb.py -c nmapdb.sql -d SQLITE-Results-$now.db {} \;
mv SQLITE-Results-$now.db ./Results-$now
#rm -rf livexmlforsqlite
#######################################
echo "Merging XML into XML-merged-$now.xml" 
python gnxmerge.py -s ./livexmlforsqlite/  > XML-merged-$now.xml
echo "Parsing Merged XML File" 
python gnxparse.py XML-merged-$now.xml -i -p -s -r -c >c> XML-output_all-$now.csv 
python gnxparse.py XML-merged-$now.xml -p >> ./Results-$now/XML-Open-Ports.txt
python gnxparse.py XML-merged-$now.xml -i >> ./Results-$now/XML-Live-IPs.txt
python gnxparse.py XML-merged-$now.xml -s >> ./Results-$now/XML-Subnets.txt
python gnxparse.py XML-merged-$now.xml -c >> ./Results-$now/XML-Host-Ports-Matrix.csv
python gnxparse.py XML-merged-$now.xml -r 'nmap -Pn -n  ' >> ./Results-$now/gnx-suggested_scans-$now.sh
#rm -rf livexmlforsqlite
echo "########All Done, Merged XML is in gnx-merged-$now.xml########"
echo "########Scan data can be found in XML* files########" 
echo "############ merging Gnmap files##########"
find . -maxdepth 1 -type f -name '*.gnmap' -print0 |  sort -z |  xargs -0 cat -- >> ./Results-$now/gnmap-merged.gnmap
echo "############parsing Gnmap files##########"
mv nmap2csv.py ./Results-$now
mv gnmap-parser.sh ./Results-$now
cd Results-$now
python nmap2csv.py  -i gnmap-merged.gnmap   -f ip-fqdn-port-protocol-service-version-os | grep -e tcp -e udp -e IP  | tr ";" ","  > gnmap-detailed.csv
bash gnmap-parser.sh -p

cd ..
#mv gnx* ./Results-$now/
cat ./Results-$now/Parsed-Results/Host-Lists/Alive-Hosts-Open-Ports.txt > ./Results-$now/Gnmap-LiveHosts.txt
cat ./Results-$now/Parsed-Results/Port-Lists/TCP-Ports-List.txt  | tr "\n" "," > ./Results-$now/Gnmap-OpenPorts.txt
echo "####Almost Done ! Compressing Files ...####"
find . -maxdepth 1 -name '*.gnmap' -print >gnmap.manifest
find . -maxdepth 1 -name '*.xml' -print >xml.manifest
find . -maxdepth 1 -name '*.nmap' -print > nmap.manifest
#tar -cvzf textfiles.tar.gz --files-from /tmp/test.manifest
#find . -name '*.' | xargs rm -v
tar -cvzf NmapFiles-$now.tar.gz --remove-files --files-from nmap.manifest
tar -cvzf XMLFiles-$now.tar.gz --exclude='XML-merged*'  --remove-files --files-from xml.manifest
tar -cvzf GnmapFiles-$now.tar.gz --remove-files --files-from gnmap.manifest
mv *.tar.gz ./Results-$now/
mv  XML-merged-$now.xml ./Results-$now/
ls Results-$now -latr | tail -n 10
echo "Have fun !"
