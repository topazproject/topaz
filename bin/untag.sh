#!/bin/bash

echo "Untagging tagged specs"
for i in `find spec/tags/ -name "*_tags.txt"`; do
    FILE="$i"
    SPECNAME="${FILE%_tags.txt}"_spec.rb
    SPECPATH="`echo "$SPECNAME" | sed 's#spec/tags/rubyspec/tags/#spec/rubyspec/#'`"
    SPECPATH="`echo "$SPECNAME" | sed 's#spec/tags/#../rubyspec/#'`"
    echo "$SPECPATH"
    timeout -s 9 30 bin/topaz ../mspec/bin/mspec tag -t $(pwd)/bin/topaz --del fails "$SPECPATH"
done

FAILING_FILES=""
echo "Tagging failing specs"
for i in `find ../rubyspec/core/kernel -name "*_spec.rb"`; do
    FILE="$i"
    echo "$FILE"
    timeout -s 9 30 bin/topaz ../mspec/bin/mspec tag -t $(pwd)/bin/topaz --add fails "$FILE" | tee output.txt
    grep "1 file, 0 examples, 0 expectations, 0 failures, 1 error" output.txt
    if [ $? -eq 0 ]; then
	# Specfile had an error during load
	FAILING_FILES="${FAILING_FILES} $FILE"
    fi
    rm -f output.txt
done

echo "These files failed to even load:"
sleep 2
echo $FAILING_FILES
