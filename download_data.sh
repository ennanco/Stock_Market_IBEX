#!/bin/sh

python get_stocks.py $1

sed -i "2d" *.csv


