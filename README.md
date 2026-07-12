# mpos-package-mpk

Reusable composite GitHub Action that builds a deterministic `.mpk` from a
MicroPythonOS app folder, following the layout and reproducibility recipe
from [Bundling Apps](https://docs.micropythonos.com/apps/bundling-apps/):
fixed timestamps, sorted entries, stored (uncompressed), app folder first.
Any repo with a standard MicroPythonOS app layout can reuse this without
modification -- the only requirement is that `MANIFEST.JSON`'s `fullname`
matches the app folder's own name (required by the bundling format anyway).

## Usage

```yaml
- name: Build .mpk
  id: build
  uses: tjorim/mpos-package-mpk@v1
  with:
    app-dir: path/to/your_app

- name: Upload artifact
  uses: actions/upload-artifact@v4
  with:
    name: your_app-mpk
    path: ${{ steps.build.outputs.mpk-path }}
```

The action provisions its own Python 3 via `actions/setup-python`, so it
doesn't depend on anything already set up in the calling workflow. Building
itself is pure stdlib (`zipfile`) -- no external `zip`/`find`/`touch` tools,
so it runs identically on Linux, macOS, and native Windows runners.

## Testing

`tests/` has both unit tests for `package_mpk.py` (built-mpk contents,
determinism across two runs, the fullname/folder-name validation) and a
`fixture-app/` used by CI to dogfood the action itself end-to-end, on
Linux, macOS, and Windows runners. Run locally with:

```
python -m unittest discover tests
```

## Why not just shell out to `zip -r`?

An earlier version of this script shelled out to `find`/`touch`/`zip`
directly. `zip -r` recurses into any directory *name* passed to it,
independent of whatever filtered file list you piped in -- so excluding
`__pycache__` from the file list alone wasn't enough, `-r` re-scanned the
filesystem and pulled it back in anyway. Building the archive directly with
Python's `zipfile` module sidesteps that class of bug entirely: each entry
is added explicitly, there's no recursive flag to misbehave.
