#! /bin/bash

set -e
args=()

coverage=( --cov-report term-missing --cov norpm --cov tests )
for arg; do
    case $arg in
    --no-coverage) coverage=() ;;
    *) args+=( "$arg" ) ;;
    esac
done

abspath=$(readlink -f .)
export PYTHONPATH="${PYTHONPATH+$PYTHONPATH:}$abspath"
"${PYTHON:-python3}" -m pytest -s tests "${coverage[@]}" "${args[@]}"
