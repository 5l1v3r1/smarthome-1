#!/bin/sh

git checkout .
while [ true ]; do
	git pull origin

	if [ $? -eq 0 ]; then
		break
	fi

	sleep 1
done

nohup python3 ev.py >> ev.log 2>&1 &

