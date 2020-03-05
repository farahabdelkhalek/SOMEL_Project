#!/bin/bash
cd contiki/examples/zolertia/zoul/range-test
cp range-test-transmit.c range-test.c
sudo make TARGET=zoul range-test.upload WITH_LCD=1 WITH_SUBGHZ=1 login
