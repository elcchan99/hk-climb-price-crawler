#!/bin/bash

gym=$1
if [ -z "$1" ]; then
    echo "Missing first argument [gym]"
    exit 1
fi

mkdir -p docs
exist_file="docs/$gym.json"
if [ ! -f $exist_file ]; then
    touch $exist_file
fi
new_file="docs/$gym-new.json"

function md5() {
    echo "$(md5sum $1 | cut -d' ' -f 1)"
}

rm -f $new_file
poetry run scrapy crawl $gym -t jsonlines -O $new_file
if [ $? -eq 0 ]; then
    old_md5="$(md5 $exist_file)"
    new_md5="$(md5 $new_file)"
    if [[ "$old_md5" != "$new_md5" ]]; then
        mv $new_file $exist_file
    else
        rm $new_file
        echo "Same content as before"
    fi
else
    echo "Fail to crawl info from Gym $gym"
    exit 1;
fi
