#!/usr/bin/env bash

DIRS=(
    app/models
    app/actions
    app/routers
)

# these are easy fixes
AUTO_FIX=(
    F401       # remove unused imports
    UP039      # parentheses after class definition
    Q002       # single quote docstring
    E401       # multiple imports on one line
    F841       # unused variables
)

for DIR in "${DIRS[@]}"
do
    for RULE in "${AUTO_FIX[@]}"
    do
        echo "Linting ${DIR} with ruff rule ${RULE}"
        ruff check ${DIR} --select ${RULE} --fix
    done
done

cat <<EOT
Suggested Git message:

Ruff linter auto-fixes for:
- Unused imports
- Unused variables
- Parentheses after class definition
- Single quote docstrings
- Multiple imports on one line

EOT
