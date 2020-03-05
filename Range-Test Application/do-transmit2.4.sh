#!/bin/bash
cd contiki/examples/zolertia/zoul/range-test
cp range-test-transmit2.4.c range-test.c
sudo make TARGET=zoul range-test.upload WITH_LCD=1 login
