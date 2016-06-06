echo    "########## Downloading GNX and gnmap-parser tools to this directory ############"
wget https://bitbucket.org/memoryresident/gnxtools/raw/fde3449ff2756686e001ac4f7a45849a187f3710/gnxparse.py &> /dev/null
wget https://bitbucket.org/memoryresident/gnxtools/raw/fde3449ff2756686e001ac4f7a45849a187f3710/gnxmerge.py &> /dev/null
wget https://raw.githubusercontent.com/royharoush/rtools/master/gnmap-parser.sh &> /dev/null
echo    "########## Download Complete ############"
echo    "########## GNX Nmap Tools Are Now Inside Your Directory ############"
echo    "########## Modified Gnmap-Parser is now Inside Your Directory ############"
echo '####removing files with no  open ports for faster processing############'
mkdir NoOpenPorts
grep -LZ "state="open"" . | while IFS= read -rd '' x; do mv "$x" ./NoOpenPorts; done
#grep -LZ "state="open"" . | while IFS= read -rd '' x; do rm "$x"; done
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
##### This can be used to remove files that doesnt have any open ports 

mkdir Combined_Results
find . -maxdepth 1 -type f -name '*.gnmap' -print0 |  sort -z |  xargs -0 cat -- >> ./Combined_Results/gnmap-merged.gnmap
echo "############parsing Gnmap files##########"
mv gnmap-parser.sh ./Combined_Results
cd Combined_Results
bash gnmap-parser.sh -p
mv ../gnx* ./
cd Combined_Results
echo "I like wearing flip flops!"
ls -latr | tail -n 10
