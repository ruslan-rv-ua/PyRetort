# Third-party licenses

PyRetort contains code from the project below. Its license requires the
copyright notice and the license text to accompany that code, so both are
reproduced here. PyRetort's own license is in [LICENSE](LICENSE).

## gen-exe

- Version: 0.2.1, released on 8 February 2021
- Author: Sil C. van de Leemput
- Repository: https://github.com/silvandeleemput/gen-exe
- Package: https://pypi.org/project/gen-exe/0.2.1/
- License: MIT

### What PyRetort uses

The code that adds an icon to the generated launcher, in
[`src/pyretort/builder/exe_generator/generate_exe.py`](src/pyretort/builder/exe_generator/generate_exe.py):
the `ICONDIRHEADER`, `ICONDIRENTRY` and `GRPICONDIRENTRY` structures, the
`DataStruct` and `Icon` classes and the `add_icon_to_exe` function.

Compared on 8 October 2026 with `genexe/winicon.py` from the gen-exe 0.2.1
wheel on PyPI, this code is the same apart from added docstrings and type
hints, wrapped long lines and a leading underscore on the helper methods;
gen-exe's `add-icon-to-exe` command was not taken over.

The launcher itself ([`launcher/launcher.c`](launcher/launcher.c)) is
PyRetort's own code. It replaced the gen-exe launcher template that
development versions before 0.1.0 used.

### License text

```text
MIT License

Copyright (c) 2021 Sil C. van de Leemput

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
