#!/usr/bin/env bash

# Flags
MAKE_FLAG=false
UP_FLAG=false
DOWN_FLAG=false
DOWN_STEPS=1  # Default number of downgrades
REVISION_NAME=""  # Default revision name

# Check if any flag is passed
if [ "$#" -eq 0 ]; then
    echo "You must provide at least one flag. Options: --make [optional name], --up, --down [optional steps]"
    exit 1
fi

# Parse flags
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --make)
            MAKE_FLAG=true
            if [[ "$2" != --* ]]; then
                REVISION_NAME="$2"
                shift
            fi
            ;;
        --up) UP_FLAG=true;;
        --down)
            DOWN_FLAG=true
            # Check if next argument is a number
            if [[ "$2" =~ ^[0-9]+$ ]]; then
                DOWN_STEPS=$2
                shift
            fi
            ;;
        *) echo "Unknown parameter: $1"; exit 1;;
    esac
    shift
done

# Check for incompatible flag combinations
if $MAKE_FLAG && ($UP_FLAG || $DOWN_FLAG); then
    echo "The --make flag cannot be combined with --up or --down."
    exit 1
fi

# Perform actions based on flags
if $MAKE_FLAG; then
    if [ -z "$REVISION_NAME" ]; then
        alembic revision --autogenerate
    else
        alembic revision --autogenerate -m "$REVISION_NAME"
    fi
fi

if $UP_FLAG; then
    alembic upgrade head
fi

if $DOWN_FLAG; then
    alembic downgrade -$DOWN_STEPS
fi
