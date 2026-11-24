$ErrorActionPreference = 'Stop'
python -m assignment3.part2 --reset --output evidence/part2_results.txt
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
