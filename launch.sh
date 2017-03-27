#!/bin/bash
# launch.sh
# launch discord bots

for ((i=0; i<$1; i++))
do
    echo "Launching shard $2 $i with command python3 dbot.py -s $i $2"
    python3 dbot.py -s $i $2 &
    sleep 10
done

echo "Launching web"
python3 webLauncher.py