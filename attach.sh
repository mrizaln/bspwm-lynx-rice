#!/usr/bin/sh

stow -t ~/.config -vS .config
cd .local
stow -t ~/.local/bin -vS bin
