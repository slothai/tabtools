# These are simple integration tests aimed to cover existing holes in unit tests. Hopefully this would be either moved
# to either python testing framework or something like that: https://github.com/sstephenson/bats
# Currently these tests are manual (not really tests, meh).
echo "No header, set autoheader"
echo -e "fields\tno\theader" | .env/bin/python -c "from tabtools.scripts import cat; cat()" -H
echo -e '\n'

echo "No header, set header"
echo -e "fields\tno\theader" | .env/bin/python -c "from tabtools.scripts import cat; cat()" -H '# field1,field2,field3'
echo -e '\n'

echo "No header, should raise error"
echo -e "fields\tno\theader" | .env/bin/python -c "from tabtools.scripts import cat; cat()" || echo 'Correctly raises error'
echo -e '\n'

echo "Has header, set autoheader"
echo -e "# header1\theader2\theader3\nfields\twith\theader" | .env/bin/python -c "from tabtools.scripts import cat; cat()" -H
echo -e '\n'

echo "Has header, set header"
echo -e "# header1\theader2\theader3\nfields\twith\theader" | .env/bin/python -c "from tabtools.scripts import cat; cat()" -H '# field1,field2,field3'
echo -e '\n'

echo "Has header"
echo -e "# header1\theader2\theader3\nfields\twith\theader" | .env/bin/python -c "from tabtools.scripts import cat; cat()"
echo -e '\n'

echo "Example of two files in the stream with autoheader. Note, argument before - would parse - as a header"
echo -e "fields\tno\theader" | .env/bin/python -c "from tabtools.scripts import cat; cat()" - <(echo -e "second\tline\there") -H
echo -e '\n'

echo "Example of two files in the stream with autoheader and no header in the output. Note, argument before - would parse - as a header"
echo -e "fields\tno\theader" | .env/bin/python -c "from tabtools.scripts import cat; cat()" - <(echo -e "second\tline\there") -NH
echo -e '\n'

echo "Example of two files in the stream with autoheader and no header in the output. Note, argument before - would parse - as a header"
echo -e "fields\tno\theader" | .env/bin/python -c "from tabtools.scripts import cat; cat()" -H -N - <(echo -e "second\tline\there")
echo -e '\n'

echo "Example of stream filtering"
cat tabtools/tests/files/sample3.tsv | python -c 'from tabtools.scripts import *; awk()' -o 'key;value' -f 'key>=value'

echo "tpretty should properly handle spaces in columns"
echo -e "# f1\tf2\ncolumn one\tcolumn two" | python -c 'from tabtools.scripts import *; pretty()'
