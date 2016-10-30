cd .. && head tabtools/tests/files/hsbc-stock.tsv \
    | python -c "from tabtools.scripts import *; grp()" \
    -k 'week=strftime("%U", DateEpoch(Date))' \
    -g "Date=FIRST(Date); Open=FIRST(Open); High=MAX(High)" \
    -g "Low=MIN(Low); Close=LAST(Close); Volume=SUM(Volume)"
