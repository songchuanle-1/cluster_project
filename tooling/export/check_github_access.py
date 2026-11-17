"""Read the authenticated GitHub identity without printing stored credentials."""
from pathlib import Path
from datetime import datetime, timezone
import json, os, subprocess, urllib.request, urllib.error

HERE=Path(__file__).resolve().parent
env=dict(os.environ,GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='never')
result={'checked_at':datetime.now(timezone.utc).isoformat(),'credentials_printed':False}
token=os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
username=None
if token:
    result['credential_source']='existing_environment'
else:
    proc=subprocess.run(['git','credential','fill'],
        input='protocol=https\nhost=github.com\n\n',text=True,capture_output=True,env=env,timeout=40)
    if proc.returncode==0:
        values=dict(line.split('=',1) for line in proc.stdout.splitlines() if '=' in line)
        token=values.get('password')
        username=values.get('username')
        result['credential_source']='existing_git_credential_manager'
    else:
        result.update(authenticated=False,credential_source='none',
            reason='No noninteractive GitHub credential was available.')
if token:
    try:
        request=urllib.request.Request('https://api.github.com/user',
            headers={'Accept':'application/vnd.github+json','Authorization':'Bearer '+token,
                'X-GitHub-Api-Version':'2022-11-28','User-Agent':'cluster-project-handoff'})
        with urllib.request.urlopen(request,timeout=25) as response:
            profile=json.load(response)
        result.update(authenticated=True,login=profile['login'],account_type=profile['type'],
            user_id=profile['id'])
    except urllib.error.HTTPError as error:
        result.update(authenticated=False,http_status=error.code,reason='GitHub identity request failed.')
    except (OSError,TimeoutError) as error:
        result.update(authenticated=False,reason='GitHub network access failed.',error_type=type(error).__name__)
HERE.mkdir(parents=True,exist_ok=True)
(HERE/'github_access.actual.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(result,ensure_ascii=False))
