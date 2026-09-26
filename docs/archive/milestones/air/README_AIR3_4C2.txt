EkoKontur AIR-3.4C2 Real Binding Fix v01

Purpose:
Fix missing user-facing Impact Forecast and bind Incident Summary data.

Changes:
- add real Impact Forecast section into Event Dashboard;
- replace empty Incident Summary payload with selected event data;
- preserve existing workflow renderer.

Apply:
python .\tools\apply_air3_4c2_real_binding_fix.py
