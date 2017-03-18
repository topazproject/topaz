#!/bin/bash

top="`cd $(dirname "$0"); cd ..; pwd`"

### Check prerequesites
if [ ! -d "$top/spec/rubyspec" ]; then
    echo "You need to checkout rubyspec in $top/spec/rubyspec"
    exit 1
fi

if [ ! -f "$top/spec/mspec/bin/mspec" ]; then
    echo "You need to checkout mspec in $top/spec/mspec"
    exit 1
fi

### Determine how to run timeout
if [ -z "$(which timeout 2>/dev/null)" ]; then
    if [ -n "$(which gtimeout 2>/dev/null)" ]; then
        TIMEOUT="gtimeout -s 9"
    else
        ################################################################################
        # Executes command with a timeout. From
        # http://unix.stackexchange.com/questions/43340/how-to-introduce-timeout-for-shell-scripting
        #
        # Params:
        #   $1 timeout in seconds
        #   rest - command
        # Returns 1 if timed out 0 otherwise
        timeout_func() {
            time=$1
            # start the command in a subshell to avoid problem with pipes
            # (spawn accepts one command)
            command_and_args="${@:2}"
            command="/bin/bash -c \"$command_and_args\""
            expect -c "set echo \"-noecho\"; set timeout $time; spawn -noecho $command; expect timeout { exit 1 } eof { exit 0 }"
            if [ $? = 1 ] ; then
                echo "Killed after ${time} seconds"
            fi
        }
        TIMEOUT="timeout_func"
    fi
else
    TIMEOUT="timeout -s 9"
fi

### Make sure we exit when pressing Ctrl+C
function control_c() {
    exit 1
}
trap control_c SIGINT

### Actually run
echo "Untagging tagged specs"
sleep 1
for i in `find spec/tags/ -name "*_tags.txt"`; do
    FILE="$i"
    SPECNAME="${FILE%_tags.txt}"_spec.rb
    SPECPATH="`echo "$SPECNAME" | sed 's#spec/tags/rubyspec/tags/#spec/rubyspec/#'`"
    SPECPATH="`echo "$SPECNAME" | sed 's#spec/tags/#spec/rubyspec/#'`"
    $TIMEOUT 15 bin/topaz spec/mspec/bin/mspec tag -t "${top}/bin/topaz" --config="${top}/topaz.mspec" --del fails "$SPECPATH"
done

FAILING_FILES=""
echo "Tagging failing specs"
sleep 1
for i in `find spec/rubyspec/core spec/rubyspec/command_line spec/rubyspec/language -name "*_spec.rb"`; do
    FILE="$i"
    $TIMEOUT 15 bin/topaz spec/mspec/bin/mspec tag -t "${top}/bin/topaz" --config="${top}/topaz.mspec" --add fails "$FILE" | tee output.txt
    grep "1 file, 0 examples, 0 expectations, 0 failures, 1 error" output.txt
    if [ $? -eq 0 ]; then
        # Specfile had an error during load
        FAILING_FILES="${FAILING_FILES} ${FILE}"
    fi
    rm -f output.txt
done

if [ -n "$FAILING_FILES" ]; then
    echo "These files failed to even load, make sure they are in ${top}/topaz.mspec"
    sleep 2
    echo $FAILING_FILES
fi
