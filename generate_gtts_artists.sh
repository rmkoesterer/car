#!/bin/bash

find /mnt/disk1/general -maxdepth 1 -mindepth 1 -type d | while read line; do \
text=`echo $a | awk -F'/' '{print $NF}'`; \
out=`echo $a | awk -F'/' '{print $NF}' | sed 's/ /_/g'`; \
echo "./gtts.sh ${text} artists/${out}"; \
done
