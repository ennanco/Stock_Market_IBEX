#!/bin/sh

#required to set at least the initial date to get the stocks
python get_stocks.py $1

sed -i "2d" *.csv


