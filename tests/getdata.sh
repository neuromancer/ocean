for p in $(cat robust_programs.csv); do
  #printf $p,
  ocean.py  -n 10 $p-report 2> /dev/null
done
