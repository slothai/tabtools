# Tabtools - SQL & streaming processing in command line

[![CircleCI Badge](https://circleci.com/gh/slothai/tabtools.svg?style=svg)](https://circleci.com/gh/slothai/tabtools)
[![PyPi version](https://img.shields.io/pypi/v/tabtools.svg)](https://pypi.org/project/tabtools/)
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Fslothai%2Ftabtools.svg?type=shield)](https://app.fossa.com/projects/git%2Bgithub.com%2Fslothai%2Ftabtools?ref=badge_shield)

### Install

```
python3 -m pip install --user tabtools
```


### Tests

```
make test
```

### Examples

Demo file consists of HSBC daily stock data.

```bash
> head tabtools/tests/files/hsbc-stock.tsv

Date  Open    High    Low Close   Volume
2014-02-21  84.35   84.45   83.9    83.45   17275.0
2014-02-24  83.85   84.4    83.75   84.35   10549.0
2014-02-25  81.65   82.3    81.6    83.9    31186.0
2014-02-26  81.15   81.65   81.0    81.65   18937.0
2014-02-27  81.85   82.4    81.0    81.15   19688.0
2014-02-28  82.25   82.45   81.8    81.9    10806.0
2014-03-05  81.4    81.7    81.15   81.5    6101.0
2014-03-06  81.5    81.75   81.05   81.4    8642.0
2014-03-07  81.3    81.45   81.05   81.45   15464.0
```

Convert daily data to weekly:

```bash

> head tabtools/tests/files/hsbc-stock.tsv \
    | ttreduce -g 'week=strftime("%U", DateEpoch(Date))' \
        -s "Date=FIRST(Date); Open=FIRST(Open); High=MAX(High)" \
        -s "Low=MIN(Low); Close=LAST(Close); Volume=SUM(Volume)" \
    | ttpretty


week | Date       | Open  | High  | Low   | Close | Volume
-----|------------|-------|-------|-------|-------|--------
07   | 2014-02-21 | 84.35 | 84.45 | 83.9  | 83.45 | 17275.0
08   | 2014-02-24 | 83.85 | 84.4  | 81.0  | 81.9  | 91166
09   | 2014-03-05 | 81.4  | 81.75 | 81.05 | 81.45 | 30207
```

Sort original file, compute 3 different EMAs (exponential moving
averages), MACD and simple moving average indicators, select last 10
lines and prettify output:

```bash
> cat tabtools/tests/files/hsbc-stock.tsv \
    | ttsort -k Date \
    | ttmap -s "*" \
        -s "fast_macd = EMA(Close, 12) - EMA(Close, 26); slow_macd = EMA(fast_macd, 9)" \
        -s "macd_histogram = fast_macd - slow_macd; ma50 = AVG(Close, 50)" \
    | tttail \
    | ttpretty

Date       | Open  | High  | Low   | Close | Volume  | fast_macd | slow_macd | macd_histogram | ma50
-----------|-------|-------|-------|-------|---------|-----------|-----------|----------------|--------
2015-07-02 | 69.55 | 69.75 | 69.3  | 70.15 | 17180.0 | -0.577588 | -0.302581 | -0.275007      | 73.7404
2015-07-03 | 69.55 | 70.25 | 69.45 | 69.55 | 13640.0 | -0.74297  | -0.390658 | -0.352311      | 73.7224
2015-07-06 | 67.6  | 68.85 | 67.0  | 69.55 | 34244.0 | -0.864075 | -0.485342 | -0.378734      | 73.6964
2015-07-07 | 68.7  | 69.0  | 68.35 | 67.9  | 15676.0 | -1.08074  | -0.604421 | -0.476315      | 73.6454
2015-07-08 | 66.2  | 67.6  | 66.0  | 68.45 | 31911.0 | -1.19429  | -0.722395 | -0.471898      | 73.5984
2015-07-09 | 67.05 | 67.5  | 65.35 | 65.75 | 29040.0 | -1.48504  | -0.874924 | -0.610114      | 73.4374
2015-07-10 | 68.1  | 68.45 | 67.0  | 67.75 | 31350.0 | -1.53636  | -1.00721  | -0.529149      | 73.2634
2015-07-13 | 69.0  | 69.05 | 67.0  | 68.1  | 16601.0 | -1.53114  | -1.112    | -0.419145      | 73.0974
2015-07-14 | 68.25 | 69.0  | 68.0  | 69.05 | 15219.0 | -1.43382  | -1.17636  | -0.257459      | 72.9294
2015-07-15 | 69.0  | 69.45 | 68.7  | 68.55 | 9676.0  | -1.38112  | -1.21731  | -0.163806      | 72.7614
```

## License
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Fslothai%2Ftabtools.svg?type=large)](https://app.fossa.com/projects/git%2Bgithub.com%2Fslothai%2Ftabtools?ref=badge_large)