"""Install/relocate a clean portable environment under an ordinary Windows account."""
import argparse,getpass,hashlib,json,os,pathlib,platform,secrets,subprocess,sys,tomllib,time,shutil
ROOT=pathlib.Path(__file__).resolve().parent;STATE=ROOT/'state'
_checked_dirs={ROOT}

def atomic_json(path,value):
 temp=path.with_name(path.name+'.writing');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8');os.replace(temp,path)

def progress(stage,**values):
 (STATE/'guard').mkdir(parents=True,exist_ok=True)
 record={'stage':stage,'time_unix':time.time(),**values};atomic_json(STATE/'guard/install-progress.json',record);print(json.dumps(record,ensure_ascii=True),flush=True)
def io_path(path):
 return pathlib.Path('\\\\?\\'+str(path.absolute())) if os.name=='nt' and not str(path).startswith('\\\\?\\') else path
def sha(path):
 path=io_path(path)
 h=hashlib.sha256()
 with path.open('rb') as f:
  while block:=f.read(1024*1024):h.update(block)
 return h.hexdigest()
def safe(relative):
 p=pathlib.PurePosixPath(relative)
 if p.is_absolute() or '..' in p.parts or ':' in relative or '\\' in relative:raise ValueError('Unsafe manifest path')
 target=ROOT/pathlib.Path(*p.parts)
 if not target.is_relative_to(ROOT):raise ValueError('Manifest escapes bundle')
 # Validate each directory once, rather than resolving every path component for every file.
 for parent in reversed(target.parents):
  if parent==ROOT or not parent.is_relative_to(ROOT) or parent in _checked_dirs:continue
  try:stat=io_path(parent).lstat()
  except FileNotFoundError:continue
  if getattr(stat,'st_file_attributes',0)&0x400:raise ValueError('Linked bundle directory rejected')
  _checked_dirs.add(parent)
 try:stat=io_path(target).lstat()
 except FileNotFoundError:pass
 else:
  if getattr(stat,'st_file_attributes',0)&0x400:raise ValueError('Linked bundle file rejected')
 return target
def env(key=''):
 result={k:v for k,v in os.environ.items() if not k.upper().startswith(('CODEX_','OPENAI_','DEEPSEEK_','DS_','DSCODEX_','NODE_REPL_','BROWSER_USE_','SKY_','PYTHON','GITHUB_','GH_','GOOGLE_','AWS_','AZURE_')) and not any(x in k.upper() for x in ('TOKEN','SECRET','PASSWORD','API_KEY','AUTH_')) and k.upper() not in ('NODE_OPTIONS','NODE_PATH','HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','NO_PROXY')}
 result.update(DSCODEX_BUNDLE_ROOT=str(ROOT),DSCODEX_STATE_ROOT=str(STATE),DSCODEX_WORKSPACE=str(STATE/'projects'),DSCODEX_USER_PROFILE=str(pathlib.Path.home()),CODEX_HOME=str(STATE/'home'),CODEX_SQLITE_HOME=str(STATE/'home/sqlite'),CODEX_CLI_PATH=str(ROOT/'assets/DeepSeekCodex/app/resources/codex.exe'),CODEX_ELECTRON_USER_DATA_PATH=str(STATE/'ui'),CODEX_APP_SERVER_FORCE_CLI='1',DEEPSEEK_API_KEY=key,PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',PYTHONIOENCODING='utf-8',GH_CONFIG_DIR=str(STATE/'gh'),USERPROFILE=str(STATE/'profile'),HOME=str(STATE/'profile'),APPDATA=str(STATE/'profile/AppData/Roaming'),LOCALAPPDATA=str(STATE/'profile/AppData/Local'),TEMP=str(STATE/'tmp'),TMP=str(STATE/'tmp'))
 result['PATH']=os.pathsep.join(str(ROOT/p) for p in ('assets/DeepSeekCodex/dependencies/python','assets/DeepSeekCodex/dependencies/python/Scripts','assets/DeepSeekCodex/app/resources/cua_node/bin','assets/DeepSeekCodex/dependencies/native/git/cmd','assets/DeepSeekCodex/dependencies/gh/bin'))+os.pathsep+os.environ.get('SystemRoot',r'C:\Windows')+r'\System32'
 return result
def resolve(value):
 if isinstance(value,str):return value.replace('{bundle}',ROOT.as_posix()).replace('{state}',STATE.as_posix()).replace('{current_user_sid}','')
 if isinstance(value,list):return [resolve(x) for x in value]
 if isinstance(value,dict):return {k:resolve(v) for k,v in value.items()}
 return value
def config(adapter_port):
 catalog=json.loads((ROOT/'CAPABILITY-CATALOG.json').read_text(encoding='utf8'));templates=resolve(json.loads((ROOT/'MCP-CONFIG-TEMPLATES.json').read_text(encoding='utf8')))
 lines=['model = '+json.dumps(catalog['model']),'model_provider = "deepseek"','sqlite_home = '+json.dumps(str(STATE/'home/sqlite')),'cli_auth_credentials_store = "file"','sandbox_mode = "workspace-write"','approval_policy = "on-request"','','[windows]','sandbox = "unelevated"','','[model_providers.deepseek]','name = "DeepSeek"','base_url = '+json.dumps(f'http://127.0.0.1:{adapter_port}/'),'env_key = "DEEPSEEK_API_KEY"','wire_api = "responses"']
 for name,item in templates['mcp'].items():
  lines+=['','[mcp_servers.'+json.dumps(name)+']','enabled = '+str(bool(item['configured_in_source'] and not item.get('requires_manual_credentials') and name!='local_literature')).lower()]
  for field in ('command','args','url'):
   if field in item:lines.append(field+' = '+json.dumps(item[field]))
  if item.get('env'):
   lines+=['[mcp_servers.'+json.dumps(name)+'.env]']+[json.dumps(k)+' = '+json.dumps(v) for k,v in item['env'].items()]
 marketplaces={'ds-primary-runtime':ROOT/'assets/DeepSeekCodex/runtime/codex-primary-runtime/plugins/openai-primary-runtime','ds-bundled':ROOT/'assets/marketplaces/openai-bundled','ds-featured':ROOT/'assets/marketplaces/ds-featured'}
 for name,path in marketplaces.items():lines+=['','[marketplaces.'+json.dumps(name)+']','source_type = "local"','source = '+json.dumps(str(path))]
 for name,item in catalog['plugins'].items():lines+=['','[plugins.'+json.dumps(name.replace('@openai-bundled','@ds-bundled'))+']','enabled = '+str(item['enabled']).lower()]
 text='\n'.join(lines)+'\n';tomllib.loads(text);return text
def restore_duplicates(manifest):
 table=ROOT/'DEDUPE.json'
 if not table.exists():return 0
 row=next((r for r in manifest['files'] if r['path']=='DEDUPE.json'),None)
 if not row or table.stat().st_size!=row['bytes'] or sha(table)!=row['sha256']:raise RuntimeError('Duplicate table integrity failed')
 data=json.loads(table.read_text(encoding='utf8'));indexed={r['path']:r for r in manifest['files']};verified={};restored=0
 import shutil
 for index,alias in enumerate(data['aliases']):
  if index%2000==0:progress('RESTORING_LOCAL_DUPLICATES',processed=index,total=len(data['aliases']),restored=restored)
  expected=indexed.get(alias['path']);source_row=indexed.get(alias['source'])
  if not expected or not source_row or (expected['bytes'],expected['sha256'])!=(alias['bytes'],alias['sha256']) or (source_row['bytes'],source_row['sha256'])!=(alias['bytes'],alias['sha256']):raise RuntimeError('Duplicate source is not byte-identical in manifest')
  target=io_path(safe(alias['path']))
  if target.exists():continue
  source=io_path(safe(alias['source']))
  if alias['source'] not in verified:
   if not source.is_file() or sha(source)!=alias['sha256']:
    immutable=io_path(safe(alias['source']+'.portable-template'))
    if not immutable.is_file() or sha(immutable)!=alias['sha256']:raise RuntimeError('Duplicate canonical source changed')
    source=immutable
   verified[alias['source']]=source
  target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(verified[alias['source']],target);restored+=1
 print(json.dumps({'byte_identical_files_restored_locally':restored,'downloads':False}),flush=True);return restored

def expose_home(manifest,old):
 """Actual CLI discovery directories, local ordinary files; preserve friend additions/edits."""
 record=STATE/'guard/managed-home.json';previous=json.loads(record.read_text(encoding='utf8')) if record.exists() else {};managed={};changed=0;custom=[]
 for index,row in enumerate(manifest['files']):
  name=row['path']
  if not name.startswith(('assets/home/skills/','assets/home/plugins/cache/')) or name.endswith('.portable-template'):continue
  relative=name.removeprefix('assets/home/').replace('plugins/cache/openai-bundled/','plugins/cache/ds-bundled/');source=io_path(safe(name));destination=io_path(safe('state/home/'+relative));destination.parent.mkdir(parents=True,exist_ok=True)
  prior=previous.get(relative);source_hash=None
  if destination.exists():
   # Only replace previous managed bytes; never erase a user's customization.
   destination_hash=sha(destination)
   source_hash=sha(source)
   if destination_hash==source_hash:managed[relative]=source_hash;continue
   if not prior or destination_hash!=prior:custom.append(relative);continue
  shutil.copyfile(source,destination);managed[relative]=source_hash or sha(source);changed+=1
  if changed%1000==0:progress('EXPOSING_NATIVE_HOME',files_copied=changed)
 atomic_json(record,managed);progress('NATIVE_HOME_READY',managed_files=len(managed),files_copied=changed,custom_files_preserved=len(custom))
def install(manifest):
 (STATE/'guard').mkdir(parents=True,exist_ok=True);progress('STARTING_INSTALL')
 restore_duplicates(manifest)
 for name in ('home/sqlite','home/tmp','ui','projects','tmp','guard','gh','profile/AppData/Roaming','profile/AppData/Local'): (STATE/name).mkdir(parents=True,exist_ok=True)
 admission_file=STATE/'guard/admission.json';old=json.loads(admission_file.read_text(encoding='utf8')) if admission_file.exists() else {};failures=[]
 journal_file=STATE/'guard/install-verified.jsonl';cached={};manifest_hash=sha(ROOT/'MANIFEST.json')
 if journal_file.exists():
  for line in journal_file.read_text(encoding='utf8').splitlines():
   try:entry=json.loads(line)
   except ValueError:continue
   # Each entry is bound to the expected content SHA and current file fingerprint below.
   # A small manifest/code update does not invalidate verified unchanged payload bytes.
   if 'path' in entry and 'verified_sha256' in entry:cached[entry['path']]=entry
 reused=0
 with journal_file.open('a',encoding='utf8') as journal:
  for index,row in enumerate(manifest['files']):
   path=io_path(safe(row['path']));expected=old.get('materialized',{}).get(row['path'],row)
   try:stat=path.stat()
   except FileNotFoundError:failures.append(row['path']);continue
   stamp=[stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns];prior=cached.get(row['path'])
   if prior and prior.get('stamp')==stamp and prior.get('verified_sha256')==expected['sha256']:reused+=1
   elif stat.st_size!=expected['bytes'] or sha(path)!=expected['sha256']:failures.append(row['path'])
   else:journal.write(json.dumps({'path':row['path'],'manifest_sha256':manifest_hash,'stamp':stamp,'verified_sha256':expected['sha256']})+'\n')
   if index%1000==0:journal.flush();progress('VERIFYING_BUNDLE',installation_files_verified=index,total_files=len(manifest['files']),failures=len(failures),previous_verified_files_reused=reused)
 if failures:raise RuntimeError('Bundle integrity failed: '+json.dumps(failures[:20]))
 materialized={}
 for row in manifest['files']:
  if not row['path'].endswith('.portable-template'):continue
  source=io_path(safe(row['path']));relative=row['path'].removesuffix('.portable-template');target=io_path(safe(relative));text=resolve(source.read_text(encoding='utf8'))
  if target.suffix=='.py':compile(text,str(target),'exec')
  if target.suffix=='.json':json.loads(text)
  target.write_text(text,encoding='utf8');materialized[relative]={'bytes':target.stat().st_size,'sha256':sha(target)}
 expose_home(manifest,old)
 # Installation never binds/listens. The supervisor later requires its own child's readiness record.
 adapter_port=old.get('adapter_port') if isinstance(old.get('adapter_port'),int) and 1024<old['adapter_port']<65536 else 20000+secrets.randbelow(40000)
 config_file=STATE/'home/config.toml'
 if config_file.exists():
  text=config_file.read_text(encoding='utf8');oldroot=old.get('bundle_root',str(ROOT))
  import re
  relocated=text
  roots={oldroot};parsed=tomllib.loads(text);templates=json.loads((ROOT/'MCP-CONFIG-TEMPLATES.json').read_text(encoding='utf8'))['mcp']
  for name,item in parsed.get('mcp_servers',{}).items():
   command=str(item.get('command','')).replace('\\','/');expected=str(templates.get(name,{}).get('command','')).replace('\\','/')
   if expected.startswith('{bundle}/assets/'):
    suffix=expected.removeprefix('{bundle}')
    if command.endswith(suffix):roots.add(command[:-len(suffix)])
  marketplace_suffixes={'ds-primary-runtime':'/assets/DeepSeekCodex/runtime/codex-primary-runtime/plugins/openai-primary-runtime','openai-bundled':'/assets/marketplaces/openai-bundled','ds-bundled':'/assets/marketplaces/openai-bundled','ds-featured':'/assets/marketplaces/ds-featured'}
  for name,item in parsed.get('marketplaces',{}).items():
   source=str(item.get('source','')).replace('\\','/');suffix=marketplace_suffixes.get(name)
   if suffix and source.endswith(suffix):roots.add(source[:-len(suffix)])
  for previous_root in roots:
   if pathlib.Path(previous_root).resolve()==ROOT:continue
   for representation in (previous_root,previous_root.replace('\\','/'),str(pathlib.Path(previous_root))):
    # TOML basic strings produced with JSON escapes include escaped Unicode root names.
    relocated=relocated.replace(json.dumps(representation)[1:-1],json.dumps(ROOT.as_posix())[1:-1])
   for degree in (4,2,1):relocated=relocated.replace(previous_root.replace('\\','\\'*degree),ROOT.as_posix())
   relocated=relocated.replace(previous_root.replace('\\','/'),ROOT.as_posix())
  relocated=re.sub(r'^sqlite_home\s*=.*$',lambda _: 'sqlite_home = '+json.dumps(str(STATE/'home/sqlite')),relocated,flags=re.M)
  relocated=re.sub(r'(?m)^(\s*\[marketplaces\.)(?:"openai-bundled"|openai-bundled)(\]\s*)$',r'\1"ds-bundled"\2',relocated)
  relocated=re.sub(r'(?m)^(\s*\[plugins\.[^\]\n]+)@openai-bundled',r'\1@ds-bundled',relocated)
  tomllib.loads(relocated)
  if relocated!=text:config_file.write_text(relocated,encoding='utf8')
 else:config_file.write_text(config(adapter_port),encoding='utf8')
 policy={'version':4,'filesystem':{str(ROOT/'assets').replace('\\','/'):'read',str(pathlib.Path.home()/'.codex').replace('\\','/'):'read',str(STATE/'projects').replace('\\','/'):'write'},'default_workspace':str(STATE/'projects'),'gui_apps':{}}
 (STATE/'guard/execution-policy.json').write_text(json.dumps(policy,indent=2),encoding='utf8')
 atomic_json(admission_file,{'manifest_sha256':sha(ROOT/'MANIFEST.json'),'materialized':materialized,'bundle_root':str(ROOT),'adapter_port':adapter_port});progress('INSTALL_COMPLETE',admission='PASS');print('Installation and relocation checks passed. Credentials and personal browser profiles were not imported.')
def main():
 p=argparse.ArgumentParser();p.add_argument('--install',action='store_true');p.add_argument('--check',action='store_true');p.add_argument('--launch',action='store_true');p.add_argument('--bridge',action='store_true');args=p.parse_args()
 if platform.system()!='Windows' or platform.machine().lower() not in ('amd64','x86_64'):raise RuntimeError('Windows x64 required')
 manifest=json.loads((ROOT/'MANIFEST.json').read_text(encoding='utf8'))
 if args.install or not (STATE/'guard/admission.json').exists():install(manifest)
 sys.path.insert(0,str(ROOT/'assets/guard'));os.environ['DSCODEX_BUNDLE_ROOT']=str(ROOT);os.environ['DSCODEX_STATE_ROOT']=str(STATE)
 from guard import check
 failures=check();print(json.dumps({'admission':'PASS' if not failures else 'FAIL','errors':failures,'target_model_API':'requires your own key','target_account_OAuth':'not migrated','COMSOL':'separate installation/license required','target_machine_acceptance':'PENDING'}))
 if failures:progress('ADMISSION_FAILED',errors=failures);return 2
 if args.check or args.install and not args.launch:return 0
 key='';credentials=ROOT/'credentials.json'
 if credentials.exists():key=json.loads(credentials.read_text(encoding='utf8')).get('deepseek_api_key','')
 if not key:key=getpass.getpass('Enter your own DeepSeek API key (not saved): ')
 if not key.strip():raise RuntimeError('A target-user API key is required')
 admission=json.loads((STATE/'guard/admission.json').read_text(encoding='utf8'));argv=[sys.executable,'-I','-B',str(ROOT/'session_supervisor.py'),'--adapter-port',str(admission['adapter_port'])]
 if args.bridge:argv+=['--bridge']
 return subprocess.call(argv,cwd=STATE/'projects',env=env(key))
if __name__=='__main__':
 try:sys.exit(main())
 except Exception as exc:
  try:progress('INSTALL_OR_START_ERROR',category=type(exc).__name__,message=str(exc))
  except OSError:pass
  print(type(exc).__name__+': '+str(exc),file=sys.stderr);sys.exit(1)
