#!/bin/bash

while [[ 1 ]]; do
	echo "starting $(date)" >> log.txt
	
	./duolingo_scraper.py

	sleep 3600
done

