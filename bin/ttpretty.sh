tmp=$(mktemp)
cat > $tmp

COLUMNWIDTHS=$(awk -F'\t' '{for (i=1; i<=NF; i++) if (length($i) > l[i]) l[i] = length($i) } END{for (i=1; i<=NF; i++) printf "%s%s", l[i], i==NF ? "" : " "}' $tmp)

# replace string "1 2 3" to "%-1s | %-2s | %-3s", $1, $2, $3
PROG=$(echo $COLUMNWIDTHS | sed 's/ /s | %-/g; s/^/"%-/; s/$/s\\n"/')$(echo $COLUMNWIDTHS | awk 'BEGIN{RS=" "}{printf ", $%s", NR}')

awk -v COLUMNWIDTHS="${COLUMNWIDTHS}" -F"\t" "BEGIN{ split(COLUMNWIDTHS, CW, \" \") }{
    printf ${PROG%}
    
    if (NR == 1) {
        for (i=1; i<=NF; i++) {
            # String multiplication in awk: https://stackoverflow.com/questions/37295695/how-to-use-printf-to-print-a-character-multiple-times#answer-37297195
            s = sprintf(\"%*s\", CW[i], \"\");
            gsub(/ /, \"-\" ,s);
            printf \"%s%s\", s, i==NF ? ORS : \"-|-\"
        }
    }
}" $tmp

rm -f $tmp
