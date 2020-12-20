#!/bin/bash
domain_list_file="all-qname.lst"
for x in $(cat "$domain_list_file")
do
  tests/test.py $x ALL 4.2.2.2 1.1.1.1 8.8.8.8 64.6.64.6
done

