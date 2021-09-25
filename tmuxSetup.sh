apt-get install tmux git  -y --force-yes --assume-yes
wget https://raw.githubusercontent.com/royharoush/rtools/master/tmux-31.conf -O ~/.tmux.conf
git clone https://github.com/tmux-plugins/tmux-resurrect ~/tmux-plugins/tmux-resurrect
git clone https://github.com/tmux-plugins/tmux-sensible.git ~/tmux-plugins/plugins/tmux-sensible
git clone https://github.com/tmux-plugins/tmux-continuum.git ~/tmux-plugins//tmux-continuum
git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
tmux source-file ~/.tmux.conf
wget https://gist.githubusercontent.com/royharoush/f4c26a20eb6db711c2fa73a5db89e4b6/raw/31e1a6dec164418d45fd8e52b7d794359d7cae57/bash_completion_tmux.sh -O /etc/bash_completion.d/tmux_completion.sh
