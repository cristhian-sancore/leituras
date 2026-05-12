import pathlib, py_compile, sys
root = pathlib.Path(__file__).parent
errors = []
for py in root.rglob('*.py'):
    try:
        py_compile.compile(str(py), doraise=True)
    except Exception as e:
        errors.append(f"{py}: {e}")
if errors:
    print('Compilation errors:')
    for err in errors:
        print(err)
    sys.exit(1)
else:
    print('All Python files compiled successfully.')
