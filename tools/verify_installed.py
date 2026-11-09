import json,subprocess,sys
from pathlib import Path
import euflab,euflab.__main__
controls=json.loads(Path(sys.argv[1]).read_text());console=sys.argv[2]
for module in [euflab,euflab.__main__]:
    assert 'site-packages'in module.__file__,module.__file__
for c in controls:
    for cmd in [[sys.executable,'-m','euflab'],[console]]:
        r=subprocess.run(cmd+['-'],input=json.dumps(c['input']),text=True,capture_output=True,check=True);report=json.loads(r.stdout);assert report==euflab.analyze(c['input']);assert euflab.verify(report)
        v=subprocess.run(cmd+['-','--verify'],input=r.stdout,text=True,capture_output=True,check=True);assert json.loads(v.stdout)==dict(valid=True,schema='euflab-v1')
print(f'Installed: {len(controls)} controls, both generation/verification entry points, two site-packages origins, outside checkout')
