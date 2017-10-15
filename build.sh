# Build individual executable, self contained files to dist folder.
# Build in the following order: __init__, six, utils, base, files, awk, scripts.
# This allows copying of scripts directly to user's ~/bin/ even if only internal
# network access is allowed and user does not have administrator's privileges.
PACKAGE_PATH="./tabtools"

function build_script {
    SCRIPT_FILENAME=./dist/t$1  # add prefir 't' to the function name
    mkdir -p ./dist

    echo "#!/usr/bin/env python" > $SCRIPT_FILENAME

    printf '# VERSION: ' >> $SCRIPT_FILENAME
    python -c 'from tabtools import __version__; print(__version__)' >> $SCRIPT_FILENAME

    echo -e "\n#####\n# __init__.py module\n#####" >> $SCRIPT_FILENAME
    cat $PACKAGE_PATH/__init__.py >> $SCRIPT_FILENAME

    echo -e "\n#####\n# six.py module\n#####" >> $SCRIPT_FILENAME
    cat $PACKAGE_PATH/six.py >> $SCRIPT_FILENAME

    echo -e "\n#####\n# utils.py module\n#####" >> $SCRIPT_FILENAME
    cat $PACKAGE_PATH/utils.py >> $SCRIPT_FILENAME

    echo -e "\n#####\n# base.py module\n#####" >> $SCRIPT_FILENAME
    cat $PACKAGE_PATH/base.py \
        | grep -vE '^from .utils import' \
        | grep -vE '^from .six import' >> $SCRIPT_FILENAME

    echo -e "\n#####\n# files.py module\n#####" >> $SCRIPT_FILENAME
    cat $PACKAGE_PATH/files.py \
        | grep -vE '^from .base import' \
        | grep -vE '^from .utils import' >> $SCRIPT_FILENAME

    echo -e "\n#####\n# awk.py module\n#####" >> $SCRIPT_FILENAME
    cat $PACKAGE_PATH/awk.py \
        | grep -vE '^from .utils import' >> $SCRIPT_FILENAME

    echo -e "\n#####\n# scripts.py module\n#####" >> $SCRIPT_FILENAME
    cat $PACKAGE_PATH/scripts.py \
        | grep -vE '^from tabtools import' \
        | grep -vE '^from .six import' \
        | grep -vE '^from .base import' \
        | grep -vE '^from .files import' \
        | grep -vE '^from .awk import' >> $SCRIPT_FILENAME

    echo -e "\n\nif __name__ == \"__main__\":\n    "$1"()" >> $SCRIPT_FILENAME
    chmod +x $SCRIPT_FILENAME
}

build_script cat
build_script tail
build_script srt
build_script awk
build_script grp
build_script pretty
build_script plot
