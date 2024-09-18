#!/bin/bash

SOURCE_PATH=$(dirname "$(readlink -f $0)")
DESTINATION_PREFIX="$HOME/.local"

if [ -n "$1" ];
then
    DESTINATION_PREFIX="${1%/}"
    echo
    while true; do
        read -p "Are you sure you want to install this program to '${DESTINATION_PREFIX}' prefix? " yn
        case $yn in
            [Yy]* ) break;;
            [Nn]* ) exit;;
            * ) echo "Please answer yes or no.";;
        esac
    done
    echo
fi

SHARE_PATH="${DESTINATION_PREFIX}/share"
APPLICATIONS_PATH="${SHARE_PATH}/applications"
BIN_PATH="${DESTINATION_PREFIX}/bin"
DESTINATION_PATH="${SHARE_PATH}/TinyPedal"

replace() {
    PATTERN="$1"
    STRING="$2"
    while read LINE; do
        echo "${LINE/${PATTERN}/${STRING}}"
    done
}

if [ ! -f "pyRfactor2SharedMemory/__init__.py" ];
then
    echo "Error: Missing files. Please, use a Linux source release file or 'git clone --recurse-submodules'."
    exit 1
fi



if [ -d "${DESTINATION_PATH}" ];
then
    if [ -w "${DESTINATION_PATH}" ];
    then
        rm -r "${DESTINATION_PATH}"
    else
        echo "Error: Insufficient privileges to update existing install."
        exit 1
    fi
fi

echo "Writing ${DESTINATION_PATH}"
cp -r "${SOURCE_PATH}" "${DESTINATION_PATH}"

if [ ! -d "${APPLICATIONS_PATH}" ]; then
    mkdir ${APPLICATIONS_PATH}
fi
echo "Writing ${APPLICATIONS_PATH}/svictor-TinyPedal.desktop"
replace "/usr/local" "${DESTINATION_PREFIX}" <"${SOURCE_PATH}/svictor-TinyPedal.desktop" >"${APPLICATIONS_PATH}/svictor-TinyPedal.desktop"

echo "Writing ${BIN_PATH}/TinyPedal"
replace "./" "${DESTINATION_PATH}/" <"${SOURCE_PATH}/TinyPedal.sh" >"${BIN_PATH}/TinyPedal"
chmod a+x "${BIN_PATH}/TinyPedal"

echo "Installation finished."
