import sys
from pathlib import Path

# hack
cwd = Path.cwd()
sys.path.append(str(cwd))
sys.path.append(str(cwd / "scripts"))

from cli.main import main

if __name__ == "__main__":
    main()
