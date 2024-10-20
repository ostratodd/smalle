#!/bin/bash

dirname=$1

mkdir -p ./"$dirname"
cd ./"$dirname"


gst-launch-1.0 -e rtspsrc location=rtsp://192.168.1.250:554/h264 ! rtph264depay ! h264parse ! nvv4l2decoder enable-max-performance=1 ! nvvidconv ! 'video/x-raw(memory:NVMM), format=RGBA' ! m.sink_0 \
               rtspsrc location=rtsp://192.168.1.251:554/h264 ! rtph264depay ! h264parse ! nvv4l2decoder enable-max-performance=1 ! nvvidconv ! 'video/x-raw(memory:NVMM), format=RGBA' ! m.sink_1 \
               nvcompositor name=m sink_0::xpos=0 sink_1::xpos=1920 ! nvvidconv ! nvv4l2h265enc ! h265parse ! splitmuxsink location=./out_%02d.mp4 max-size-time=1800000000000 sync=true
# 60000000000 ns = 1 minute
# so records for 30 minutes max per call 
