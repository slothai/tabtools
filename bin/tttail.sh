# tee >(head -n1) >/dev/null | >(tail "$@")
# Reference implementation: https://unix.stackexchange.com/questions/28503/how-can-i-send-stdout-to-multiple-commands
# { { tee /dev/fd/3 | head -n1 >&9; } 3>&1 | tail -qn+2 | tail "$@" >&9; } 9>&1

tmp=$(mktemp)
cat > $tmp
head -n1 $tmp
tail -qn+2 $tmp | tail "$@"
rm -rf "$tmp"
