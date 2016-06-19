echo    "########## Downloading GNX and gnmap-parser tools to this directory ############"
wget https://bitbucket.org/memoryresident/gnxtools/raw/fde3449ff2756686e001ac4f7a45849a187f3710/gnxparse.py &> /dev/null
wget https://bitbucket.org/memoryresident/gnxtools/raw/fde3449ff2756686e001ac4f7a45849a187f3710/gnxmerge.py &> /dev/null
wget https://raw.githubusercontent.com/royharoush/rtools/master/gnmap-parser.sh &> /dev/null
echo    "########## Download Complete ############"
echo    "########## GNX Nmap Tools Are Now Inside Your Directory ############"
echo    "########## Modified Gnmap-Parser is now Inside Your Directory ############"
echo '####removing files with no  open ports for faster processing############'
### echo all the files with no open ports in them 
#find -name '*.xml'   | xargs -I{} grep -LZ "state=\"open\"" {} | while IFS= read -rd '' x; do echo "$x" ; done 
#mkdir NoOpenPorts
#grep -LZ \"state="open\"\" *.xml | while IFS= read -rd '' x; do mv "$x" ./NoOpenPorts; done
#grep -LZ "state="open\"" *.xml | while IFS= read -rd '' x; do echo "$x"; done
##### This can be used to remove files that doesnt have any open ports 
#### USE WITH CAUTION, NOT FULLY TESTED #grep -LZ "state="open"" *.xml | while IFS= read -rd '' x; do rm "$x"; done ######## USE WITH CAUTION, NOT FULLY TESTED 
echo "I will now parse all your XMLs into one file called gnx-merged.xml" 
python gnxmerge.py -s ./  > gnx-merged.xml
echo "I will now create the outputs of your scans from the XML file" 
python gnxparse.py gnx-merged.xml -i -p -s -r -c >> gnx-output_all.csv 
python gnxparse.py gnx-merged.xml -p >> gnx-Open-Ports.csv 
python gnxparse.py gnx-merged.xml -i >> gnx-Live-IPs.csv
python gnxparse.py gnx-merged.xml -s >> gnx-Subnets.csv 
python gnxparse.py gnx-merged.xml -c >> gnx-Host-Ports-Matrix.csv  
python gnxparse.py gnx-merged.xml -r 'nmap -A' >> ./gnx-suggested_scans.sh
echo "########All Done, Merged XML is in gnx-merged.xml########"
echo "########Scan data can be found in gnx* files########" 
echo "############parsing Gnmap files##########"
mkdir Results
find . -maxdepth 1 -type f -name '*.gnmap' -print0 |  sort -z |  xargs -0 cat -- >> ./Results/gnmap-merged.gnmap
echo "############parsing Gnmap files##########"
mv gnmap-parser.sh ./Results
cd Results
bash gnmap-parser.sh -p
mv ../gnx* ./
#cd Results
cat ./Parsed-Results/Host-Lists/Alive-Hosts-Open-Ports.txt > Gnmap-$(date +"%d-%m-%y"-"%T" |tr ":" "-")-LiveHosts.txt
cat ./Parsed-Results/Port-Lists/TCP-Ports-List.txt  | tr "\n" "," > Gnmap-$(date +"%d-%m-%y"-"%T" |tr ":" "-")-OpenPorts.txt
echo "#### Downloading nmapParse.sh####"
#https://raw.githubusercontent.com/royharoush/rtools/master/nmapParse.sh &> /dev/null
#echo "#### To parse again run 'bash nmapParse.sh' ####"
echo "I like wearing flip flops!"
ls ./Results -latr | tail -n 10
#rm -- "$0"
