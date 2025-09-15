Master Ops Pack
===============

This archive contains everything to run the HeartCore portal workflow:

Included:
- HeartCore_Suite_v1_1.zip        -> Safe multi-window launcher (auto-extract + discover + launch)
- daily_ops_bundle.zip            -> Daily security/performance/transcendence/cultural manifests
- heartcore_wormlab_manifest.yaml -> Test suite manifest (YAML)
- heartcore_wormlab_manifest.json -> Test suite manifest (JSON)
- run_manifest_local.sh           -> Local runner (Linux/macOS)
- Run-Manifest-Local.ps1          -> Local runner (Windows)
- README_TestSuite.txt            -> Notes for the test suite
- README_DailyOps.txt             -> Notes for daily ops

Quick Start (Linux/macOS):
1) Extract this Master_Ops_Pack.zip
2) Extract HeartCore_Suite_v1_1.zip
3) cd HeartCore_Suite_v1_1
4) chmod +x RUN_ALL.sh
5) ./RUN_ALL.sh

Quick Start (Windows):
1) Extract this Master_Ops_Pack.zip
2) Extract HeartCore_Suite_v1_1.zip
3) Open the extracted folder and run RUN_ALL.bat or Run-Manifest-Local.ps1

Then plug daily_ops_bundle.zip manifests into your Sintra pipeline scheduler.
