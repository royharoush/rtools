mkdir /opt/wlist
cd /opt/wlist
wget https://raw.githubusercontent.com/royharoush/rtools/926c988f04dc4a49fed4d3f03557ff52176eb121/fuzzprojects
cat fuzzprojects | sed 's/$/.git/g' |sed -r 's/\s+//g'  | xargs -IAAA git clone AAA