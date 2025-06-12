#!/bin/bash

trap "echo 'Stopping scripts...'; pkill -P $$; exit" SIGINT SIGTERM

./app/etc/set_latency_timer 1 ttyUSB*

python3 app/frame/frame_server.py &
python3 app/board/board_server.py &
python3 app/slide/slide_server.py $1 &

wait
