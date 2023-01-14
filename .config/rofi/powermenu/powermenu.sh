#!/usr/bin/env bash

## Author  : Aditya Shakya
## Mail    : adi1090x@gmail.com
## Github  : @adi1090x
## Twitter : @adi1090x

# Available Styles
# >> Created and tested on : rofi 1.6.0-1
#
# column_circle     column_square     column_rounded     column_alt
# card_circle     card_square     card_rounded     card_alt
# dock_circle     dock_square     dock_rounded     dock_alt
# drop_circle     drop_square     drop_rounded     drop_alt
# full_circle     full_square     full_rounded     full_alt
# row_circle      row_square      row_rounded      row_alt

theme="table"
dir="$HOME/.config/rofi/powermenu"


uptime=$(uptime | awk -F 'up' '{print $2}' | cut -d, -f1)
uptime=${uptime// /}  # remove any space

rofi_command="rofi -theme $dir/$theme"

# Options
# shutdown="⏻"
# reboot="⟳"
# lock="⊘"
# suspend="⏾"
# logout="⏼"

shutdown="shutdown"
reboot="reboot"
lock="lock"
suspend="suspend"
logout="logout"


# Confirmation
confirm_exit() {
	rofi -dmenu\
		-i\
		-no-fixed-num-lines\
		-p "$1"\
		-theme $dir/confirm.rasi
}

# Message
msg() {
	rofi -theme "$dir/message.rasi" -e "Available Options  -  yes / y / no / n"
}

# Action
action() {
    chosen="$1"
    case $chosen in
        $shutdown)
    		ans=$(confirm_exit "Shutdown? " &)
    		if [[ $ans == "yes" || $ans == "YES" || $ans == "y" || $ans == "Y" ]]; then
    			systemctl poweroff
    		elif [[ $ans == "no" || $ans == "NO" || $ans == "n" || $ans == "N" ]]; then
    			exit 0
            else
    			msg
            fi
            ;;
        $reboot)
    		ans=$(confirm_exit "Reboot? " &)
    		if [[ $ans == "yes" || $ans == "YES" || $ans == "y" || $ans == "Y" ]]; then
    			systemctl reboot
    		elif [[ $ans == "no" || $ans == "NO" || $ans == "n" || $ans == "N" ]]; then
    			exit 0
            else
    			msg
            fi
            ;;
        $lock)
    		if [[ -f /usr/local/bin/betterlockscreen ]]; then
    			betterlockscreen -l &
#                lock_screen_with_blur_bg.sh
    		elif [[ -f /usr/bin/i3lock ]]; then
    			i3lock -i ~/.config/lock_wallpaper
    		fi
            ;;
        $suspend)
#			action $lock
			systemctl suspend
            ;;
        $logout)
    		ans=$(confirm_exit "Logout? " &)
    		if [[ $ans == "yes" || $ans == "YES" || $ans == "y" || $ans == "Y" ]]; then
    			if [[ "$DESKTOP_SESSION" == "Openbox" ]]; then
    				openbox --exit
    			elif [[ "$DESKTOP_SESSION" == "bspwm" ]]; then
    				bspc quit
    			elif [[ "$DESKTOP_SESSION" == "i3" ]]; then
    				i3-msg exit
    			fi
    		elif [[ $ans == "no" || $ans == "NO" || $ans == "n" || $ans == "N" ]]; then
    			exit 0
            else
    			msg
            fi
            ;;
    esac
}

main() {
    # Variable passed to rofi
    # options="$shutdown\n$reboot\n$lock\n$suspend\n$logout"
    options="$lock\n$suspend\n$logout\n$reboot\n$shutdown"


    chosen="$(echo -e "$options" | $rofi_command -p "Uptime: ($uptime)" -dmenu -selected-row 2)"

    action "$chosen"
}

main
