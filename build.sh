# Build individual executables (self contained files).
# Build in the following order: __init__, utils, base, files, awk, scripts.
# This allows copying of scripts directly to user's ~/bin/ even if only internal
# network access is allowed and user does not have administrator's privileges.
PACKAGE_PATH=$(pwd)"/tabtools"
BUILD_PATH=$(pwd)"/dist"

build_script() {
    SCRIPT_FILENAME=$BUILD_PATH/t$1  # add prefir 't' to the function name
    mkdir -p $BUILD_PATH

    echo "#!/usr/bin/env python3" > $SCRIPT_FILENAME

    printf '# VERSION: ' >> $SCRIPT_FILENAME
    python -c 'from tabtools import __version__; print(__version__)' >> $SCRIPT_FILENAME

    # Prefix every line in LICENSE with "# "
    cat LICENSE | sed "s/^/# /" >> $SCRIPT_FILENAME

    # Loop over modules and concatenate their content.
    # Remove relative imports as they would be available after concatenation.
    for module in '__init__.py' 'utils.py' 'base.py' 'files.py' 'awk.py' 'scripts.py'
    do
        echo -e "\n#####\n# $module module\n#####" >> $SCRIPT_FILENAME
        cat $PACKAGE_PATH/$module \
            | grep -vE '^from tabtools import' \
            | grep -vE '^from .base import' \
            | grep -vE '^from .utils import' \
            | grep -vE '^from .files import' \
            | grep -vE '^from .awk import' >> $SCRIPT_FILENAME
    done

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
