"""Use bundled Python 3.13 and reviewed packages without an original venv/.pth execution."""
import os,pathlib,runpy,sys
ROOT=pathlib.Path(__file__).resolve().parent
PACKAGES=ROOT/'assets/science313/Lib/site-packages'
if len(sys.argv)<2:raise SystemExit('A bundled script is required')
script=pathlib.Path(sys.argv[1]).resolve()
if not script.is_relative_to(ROOT/'assets') or not script.is_file():raise SystemExit('Script must be inside bundled assets')
sys.path[:0]=[str(script.parent)]+[str(PACKAGES/x) for x in ('','win32','win32/lib','pythonwin')]
_dll=os.add_dll_directory(str(PACKAGES/'pywin32_system32'))
sys.argv=sys.argv[1:]
runpy.run_path(str(script),run_name='__main__')
