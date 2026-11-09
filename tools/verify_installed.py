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

import euflab.atlas
assert 'site-packages' in euflab.atlas.__file__
atlas_controls=json.loads(Path(sys.argv[3]).read_text());atlas_console=str(Path(console).with_name('euflab-atlas'))
for c in atlas_controls:
    for cmd in [[sys.executable,'-m','euflab.atlas'],[atlas_console]]:
        r=subprocess.run(cmd+['-'],input=json.dumps(c['input']),text=True,capture_output=True,check=True);report=json.loads(r.stdout);assert report==euflab.atlas.analyze(c['input']);assert euflab.atlas.verify(report)
        v=subprocess.run(cmd+['-','--verify'],input=r.stdout,text=True,capture_output=True,check=True);assert json.loads(v.stdout)==dict(valid=True,schema='euflab-atlas-v1')
print(f'Installed atlas: {len(atlas_controls)} controls, both entry points, third site-packages origin, outside checkout')

import euflab.cardinality
assert 'site-packages' in euflab.cardinality.__file__
card_controls=json.loads(Path(sys.argv[4]).read_text());card_console=str(Path(console).with_name('euflab-cardinality'))
for c in card_controls:
    for cmd in [[sys.executable,'-m','euflab.cardinality'],[card_console]]:
        r=subprocess.run(cmd+['-'],input=json.dumps(c['input']),text=True,capture_output=True,check=True);report=json.loads(r.stdout);assert report==euflab.cardinality.analyze(c['input']);assert euflab.cardinality.verify(report)
        v=subprocess.run(cmd+['-','--verify'],input=r.stdout,text=True,capture_output=True,check=True);assert json.loads(v.stdout)==dict(valid=True,schema='euflab-cardinality-v1')
print(f'Installed cardinality: {len(card_controls)} controls, both entry points, fourth site-packages origin, outside checkout')

import euflab.planner
assert 'site-packages' in euflab.planner.__file__
planner_controls=json.loads(Path(sys.argv[5]).read_text());planner_console=str(Path(console).with_name('euflab-planner'))
for c in planner_controls:
    for cmd in [[sys.executable,'-m','euflab.planner'],[planner_console]]:
        r=subprocess.run(cmd+['-'],input=json.dumps(c['input']),text=True,capture_output=True,check=True);report=json.loads(r.stdout);assert report==euflab.planner.analyze(c['input']);assert euflab.planner.verify(report)
        v=subprocess.run(cmd+['-','--verify'],input=r.stdout,text=True,capture_output=True,check=True);assert json.loads(v.stdout)==dict(valid=True,schema='euflab-planner-v1')
print(f'Installed planner: {len(planner_controls)} controls, both entry points, fifth site-packages origin, outside checkout')
