import os
import subprocess
import sys
from pathlib import Path

os.environ["MPLCONFIGDIR"] = "/tmp/lab03-mpl"
os.environ["COVERAGE_FILE"] = "/results/.coverage"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
# The slim image lacks Git; install it before collecting repository tests.
sources = Path("/etc/apt/sources.list.d/debian.sources")
sources.write_text(sources.read_text().replace("http://", "https://"))
with Path("/results/system-install.log").open("w") as log:
    for command in (["apt-get", "update", "-qq"], ["apt-get", "install", "-y", "--no-install-recommends", "git"]):
        installed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        if installed.returncode:
            print(Path("/results/system-install.log").read_text()[-7000:])
            raise SystemExit(installed.returncode)
with Path("/results/install.log").open("w") as log:
    installed = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements-dev.txt"], stdout=log, stderr=subprocess.STDOUT)
if installed.returncode:
    print(Path("/results/install.log").read_text()[-7000:])
    raise SystemExit(installed.returncode)
subprocess.run([sys.executable, "-m", "pip", "list", "--format=json"], stdout=Path("/results/packages.json").open("w"), check=True)
raise SystemExit(subprocess.call([sys.executable, "-m", "pytest", "-q", "--basetemp=/tmp/pytest-lab03",
    "-o", "cache_dir=/tmp/pytest-cache", "--cov=src", "--cov-report=term-missing",
    "--cov-report=json:/results/coverage.json", "--cov-fail-under=96", "--junitxml=/results/junit.xml"]))
