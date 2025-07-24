# Contributing

Please run the formatter before pushing changes so CI passes.

```bash
make fix
```

Running `make fix` formats the codebase using Ruff and other tools. The CI pipeline executes `make check` to verify formatting without writing files. If formatting or lint fails, CI will reject the commit.

