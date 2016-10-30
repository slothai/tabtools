cd .. && cat tabtools/tests/files/hsbc-stock.tsv \
    | python -c "from tabtools.scripts import *; srt()" -k Date \
    | python -c "from tabtools.scripts import *; awk()" -o "Date; Open; High; Low; Close; Volume" \
    -o "fast_macd = EMA(Close, 12) - EMA(Close, 26); slow_macd = EMA(fast_macd, 9)" \
    -o "macd_histogram = fast_macd - slow_macd; ma50 = AVG(Close, 50)" \
    | python -c "from tabtools.scripts import *; ttail()" \
    | python -c "from tabtools.scripts import *; pretty()"
