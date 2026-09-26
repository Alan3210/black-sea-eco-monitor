EkoKontur AIR-2.1D3C Dashboard Switch Fix v01

Fix:
Replace temporary Dashboard mode throw with real return flow.

The previous code stopped with:
throw new Error('Dashboard mode active');

New behavior:
- hide legacy app;
- mount dashboard;
- stop main bootstrap safely.

Install:
python .\tools\install_air2_1d3c_fix_throw_v01.py
