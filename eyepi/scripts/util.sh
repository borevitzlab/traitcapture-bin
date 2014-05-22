#!/bin/bash

# puts the current timer in nanoseconds into the global shell variable NOW
function getNow {
	NOW=$(cat /proc/timer_list | grep 'now at' | grep -oP '\d+')
}


# puts the time since the last getNow, or an empty string, into the global var TIMER_SECS
function secTimer {
	thisNow=$(cat /proc/timer_list | grep 'now at' | grep -oP '\d+')
	if [ -z "$NOW" ]
	then
		TIMER_SECS=""
	else
		TIMER_SECS=$(( $(( $thisNow - $NOW )) / 1000000000 ))
	fi
}
