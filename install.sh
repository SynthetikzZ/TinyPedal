#!/bin/bash

SOURCE_PATH=$(dirname "$(readlink -f $0)")

replace() {
    PATTERN="$1"
    STRING="$2"
    while read LINE; do
        echo "${LINE/${PATTERN}/${STRING}}"
    done
}

install_to() {
    SHARE_PATH="${DESTINATION_PREFIX}/share"
    APPLICATIONS_PATH="${SHARE_PATH}/applications"
    BIN_PATH="${DESTINATION_PREFIX}/bin"
    DESTINATION_PATH="${SHARE_PATH}/TinyPedal"

    if [ -w "${SHARE_PATH}" ]; then
        cp -r "${SOURCE_PATH}" "${DESTINATION_PATH}"
        chown $USER "${DESTINATION_PATH}"
    else
        sudo cp -r "${SOURCE_PATH}" "${DESTINATION_PATH}"
        sudo chown $USER "${DESTINATION_PATH}"
    fi
    echo "Writing ${DESTINATION_PATH}"
    if [ ! -d "${APPLICATIONS_PATH}" ]; then
        if [ -w "${SHARE_PATH}" ]; then
            mkdir ${APPLICATIONS_PATH}
        else
            sudo mkdir ${APPLICATIONS_PATH}
        fi
        echo "creating applications directory"
    fi

    echo "Writing ${APPLICATIONS_PATH}/svictor-TinyPedal.desktop"
    if [ -w "${APPLICATIONS_PATH}" ]; then
        replace "/usr/local" "${DESTINATION_PREFIX}" <"${SOURCE_PATH}/svictor-TinyPedal.desktop" >"${APPLICATIONS_PATH}/svictor-TinyPedal.desktop"
    else
        replace "/usr/local" "${DESTINATION_PREFIX}" <"${SOURCE_PATH}/svictor-TinyPedal.desktop" | sudo tee "${APPLICATIONS_PATH}/svictor-TinyPedal.desktop" > /dev/null
    fi

    echo "Writing ${BIN_PATH}/TinyPedal"
    if [ -w "${BIN_PATH}" ]; then
        replace "./" "${DESTINATION_PATH}/" <"${SOURCE_PATH}/TinyPedal.sh" >"${BIN_PATH}/TinyPedal"
        chmod a+x "${BIN_PATH}/TinyPedal"
    else
        replace "./" "${DESTINATION_PATH}/" <"${SOURCE_PATH}/TinyPedal.sh" | sudo tee "${BIN_PATH}/TinyPedal" > /dev/null
        sudo chmod a+x "${BIN_PATH}/TinyPedal"
    fi
    echo ""
    echo "Installation finished."
}

path_approval() {
    echo ""
    echo "Are you sure you want to install TinyPedal to '${DESTINATION_PREFIX}' prefix?"
    select yn in "yes" "go back" "exit"; do
        case $yn in
            1|"yes"      )   install_to;exit;;
            2|"go back"  )   main_menu;;
            3|"exit"     )   exit;;
        esac
    done
}

remove() {
    sudo rm -r "${OLDINSTALL}/share/TinyPedal"
    sudo rm "${OLDINSTALL}/share/applications/svictor-TinyPedal.desktop"
    sudo rm "${OLDINSTALL}/bin/TinyPedal"
}


set_path() {
    echo ""
    echo "desired installation path:"
    read CUSTOMPATH
    DESTINATION_PREFIX=${CUSTOMPATH%/}
}


main_menu() {
    echo ""
    echo "  _______ _             _____         _       _ "
    echo " |__   __(_)           |  __ \       | |     | |"
    echo "    | |   _ _ __  _   _| |__) |__  __| | __ _| |"
    echo "    | |  | | '_ \| | | |  ___/ _ \/ _\` |/ _\` | |"
    echo "    | |  | | | | | |_| | |  |  __/ (_| | (_| | |"
    echo "    |_|  |_|_| |_|\__, |_|   \___|\__,_|\__,_|_|"
    echo "                   __/ |                        "
    echo "                  |___/                         "
    echo ""
    echo "Welcome to the TinyPedal installer! Choose from below options"
    echo "Installing as single user requires \$HOME/.local/bin in \$PATH to be able to start TinyPedal from Commandline."
    echo "You cannot update or remove TinyPedal with this installer if you choose a custom installation path."
    echo ""
    select yn in "single user" "all users(with root privileges)" "custom installation path" "exit"; do
        case $yn in
            1|"single user"                      )   DESTINATION_PREFIX="$HOME/.local";path_approval;;
            2|"all users(with root privileges)"  )   DESTINATION_PREFIX="/usr/local";path_approval;;
            3|"custom installation path"         )   set_path;path_approval;;
            4|"exit"                             )   exit;;
        esac
    done
}


install_found() {
    echo ""
    echo "  _______ _             _____         _       _ "
    echo " |__   __(_)           |  __ \       | |     | |"
    echo "    | |   _ _ __  _   _| |__) |__  __| | __ _| |"
    echo "    | |  | | '_ \| | | |  ___/ _ \/ _\` |/ _\` | |"
    echo "    | |  | | | | | |_| | |  |  __/ (_| | (_| | |"
    echo "    |_|  |_|_| |_|\__, |_|   \___|\__,_|\__,_|_|"
    echo "                   __/ |                        "
    echo "                  |___/                         "
    echo ""
    echo "existing installation of TinyPedal found under ${OLDINSTALL}/share/TinyPedal/. Select an option:"
    echo ""
    select yn in "update" "remove" "exit"; do
        case $yn in
            1|"update"   )   remove;DESTINATION_PREFIX=$OLDINSTALL;install_to;exit;;
            2|"remove"   )   remove;main_menu;;
            3|"exit"     )   exit;;
        esac
    done


}


if [ ! -e "pyRfactor2SharedMemory/__init__.py" ];
then
    echo "Error: Missing files. Please, use a Linux source release file or 'git clone --recurse-submodules'."
    exit 1
fi

if [ -d "/usr/local/share/TinyPedal"  ];
then
    OLDINSTALL="/usr/local"
    install_found

elif [ -d "$HOME/.local/share/TinyPedal" ];
then
    OLDINSTALL="$HOME/.local"
    install_found
fi


if [ -n "$1" ];then DESTINATION_PREFIX=${1%/};path_approval;fi;

if [ ! "$1" ];then main_menu;fi;

