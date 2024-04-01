#!/usr/bin/env bash

# change this according to the installed device name on the computer
device="wlo1"

theme="networktable.rasi"
dir="$HOME/.config/rofi/network-manager"
rofi_command="rofi -theme $dir/$theme"

get_status()
{
    local device_status=($(timeout 5s nmcli device status | grep "$device"))

    case "${device_status[2]}" in
        'connected')
            echo "$device connected to ${device_status[3]}"
            ;;
        'disconnected')
            echo "Not Connected"
            ;;
        '')
            echo -e "${device} device not found\nOR nmcli not responding" | $rofi_command -dmenu -markup-rows -i -p "Status"
            exit 1
            ;;
        *)
            echo -e "${device} device is ${device_status[2]}" | $rofi_command -dmenu -markup-rows -i -p "Status"
            exit 1
            ;;
    esac
}

get_list()
{
    local head="$(nmcli device wifi list ifname ${device} | head -1)"
    local offset_of_MODE=$(echo "$head" | head -1 | awk -F 'MODE' '{print $1}')
    local offset_m="${#offset_of_MODE}"

    local offset_of_SIGNAL=$(echo "$head" | head -1 | awk -F 'SIGNAL' '{print $1}')
    local offset_s="${#offset_of_SIGNAL}"

    while read line; do
        if [[ "${line:0:1}" == "*" ]]; then
            line="${line:8:-1}"
        fi

        local ssid="$(echo "$line" | cut -b20-$(( offset_m - 9 )))"
        local signal="$(echo "$line" | cut -b$(( offset_s  ))- | tr -s ' ' | cut -d ' ' -f2)"

        echo "$ssid| $signal |"
    done < <(nmcli device wifi list ifname "$device" | tail -n+2)
}

prompt()
{
    local add=""
    if [[ "$1" == "password" ]]; then
        add="-password"
    fi

    rofi -i $add -no-fixed-num-lines -theme "${dir}/prompt.rasi" -dmenu -p "${1}: "
}

connect_hidden()
{
    local ssid="$1"
    local password="$2"

    nmcli connection add type wifi con-name "$ssid" ifname "$device" ssid "$ssid" #&&\
    nmcli connection modify "$ssid" wifi-sec.key-mgmt wpa-psk #&&\
    nmcli connection modify "$ssid" wifi-sec.psk "$password" #&&\
    nmcli connection up "$ssid"
}

connect()
{
    shopt -s extglob
    local ssid="$1"
    local ssid="${ssid%%*([[:blank:]])}"
    local hidden="no"

    if [[ "$ssid" == "" ]]; then
        exit 0;
    elif [[ "$ssid" == "[hidden]" ]]; then
        ssid="$(prompt "ssid")"
        hidden="yes"
    fi

    # check whether the computer has connected to the network before (the network details is saved in the computer)
    local promt_password=true
    while read c; do
        if [[ "$c" =~ ^${ssid}.* ]]; then
            promt_password=false
            break
        fi
    done < <(ls /etc/NetworkManager/system-connections/ | cut -d. -f1)

    local result=""
    if [[ "$promt_password" == true ]]; then
        password="$(prompt "password")"
        if [[ "$password" == "" ]]; then
            exit 0
        fi
        notify-send "connecting..."
        result=$(connect_hidden "$ssid" "$password" 2>&1)
    else
        notify-send "connecting..."
        result=$(nmcli device wifi connect "$ssid" hidden on 2>&1)
    fi

    notify-send "$result"
}

main() 
{
    local status=$(get_status)
    [ $? -ne 0 ] && exit 1

    local list=$(echo -e "$(get_list)\n[disconnect]\n[hidden]")

    local ssid="$(echo "$list" | $rofi_command -dmenu -markup-rows -i -p "$status")"
    if [[ "$ssid" == "[disconnect]" ]]; then
        local msg=$(nmcli device disconnect "$device")
        notify-send "$msg"
        exit 0
    fi

    local ssid="$(echo "$ssid" | cut -d '|' -f1)"

    connect "$ssid"
}

main
