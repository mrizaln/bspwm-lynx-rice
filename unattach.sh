#!/usr/bin/sh

stow -t ~/.config -vD .config
cd .local
stow -t ~/.local/bin -vD bin
