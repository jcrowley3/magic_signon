# Linting with Ruff

## TL;DR

Ruff is a linter.  Linting is the process of running a program that will analyse code for potential errors.

- [ruff](https://github.com/astral-sh/ruff)
- [rules](https://beta.ruff.rs/docs/rules/)
- Configuration is in `puproject.toml`

## Examples

- `ruff check app/models` - Run linter on all of `app/models`
- `ruff check app/models --select UP007` - Run linter on all of `app/models` only for rule UP007
- `ruff check app/models --ignore UP007` - Run linter on all of `app/models` and ignore rule UP007
- `ruff check app/models --fix` - Auto-fix the easy ones

## Notes

- We probably want to ignore UP007 (`Use X | Y for type annotations`)

## Tabs versus Spaces, Oh My

pycodestyle rule W191 says that spaces are preferred over tabs.

Potential one-time fix:

```
sudo apt-get install moreutils
find ./ -iname '*.java' -type f -exec bash -c 'expand -t 4 "$0" | sponge "$0"' {} \;
```

## E401

The [E401](https://beta.ruff.rs/docs/rules/multiple-imports-on-one-line/) rule appears to maybe be incompatiable with imports like `from pydantic import Field, validator`.
