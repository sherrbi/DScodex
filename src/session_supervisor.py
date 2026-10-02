"""One explicitly launched session; stop only children started by this process."""
import argparse,json,os,pathlib,queue,secrets,shutil,socket,subprocess,sys,threading,time
ROOT=pathlib.Path(__file__).resolve().parent;STATE=ROOT/'state'
sys.path.insert(0,str(ROOT/'assets/guard'))
sys.path.insert(0,str(ROOT))
from owned_process import OwnedProcess
def port():
 with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--bridge',action='store_true');p.add_argument('--adapter-port',type=int,required=True);args=p.parse_args()
 from guard import check
 env=dict(os.environ);env.update(DSCODEX_BUNDLE_ROOT=str(ROOT),DSCODEX_STATE_ROOT=str(STATE),DSCODEX_SESSION_LAUNCH='1')
 children=[]
 try:
  def spawn(argv):
   child=OwnedProcess(argv,STATE/'projects',env);children.append(child);child.stdin.close()
   threading.Thread(target=lambda:drain(child.stderr),daemon=True).start();return child
  def drain(stream):
   while stream.read(65536):pass
  adapter=spawn([sys.executable,'-I','-B',str(ROOT/'assets/DeepSeekCodex/ds_wire_adapter.py'),'--port',str(args.adapter_port),'--codex-home',str(STATE/'home'),'--log-dir',str(STATE/'wire-adapter')])
  if args.bridge:
   bridge_port=port();env['DS_BRIDGE_PORT']=str(bridge_port);env['DSCODEX_BRIDGE_TOKEN']=secrets.token_hex(32)
   extension=STATE/'live-chrome/extension'
   if extension.exists():raise RuntimeError('Bridge session extension already exists; review/reset that specific state directory explicitly')
   shutil.copytree(ROOT/'assets/live-chrome/extension',extension)
   (extension/'portable-session.js').write_text('const PORTABLE_BRIDGE_SESSION = '+json.dumps({'base':f'http://127.0.0.1:{bridge_port}','token':env['DSCODEX_BRIDGE_TOKEN']})+';\n',encoding='utf8')
   bridge=spawn([sys.executable,'-I','-B',str(ROOT/'assets/live-chrome/bridge.py')]);threading.Thread(target=lambda:drain(bridge.stdout),daemon=True).start()
   print('Fresh browser extension prepared. Load state/live-chrome/extension into a separate empty browser profile explicitly. No personal profile is attached.')
  # Fail closed if our adapter cannot bind; never attach to a pre-existing listener.
  ready=queue.Queue();threading.Thread(target=lambda:ready.put(adapter.stdout.readline()),daemon=True).start()
  try:line=ready.get(timeout=15)
  except queue.Empty:raise RuntimeError('Owned adapter readiness timeout')
  if adapter.poll() is not None or b'ds-wire-adapter ' not in line or b' listening on ' not in line:raise RuntimeError('Owned adapter failed to bind; refusing any pre-existing listener')
  threading.Thread(target=lambda:drain(adapter.stdout),daemon=True).start()
  app=spawn([str(ROOT/'assets/DeepSeekCodex/app/ChatGPT.exe'),'--user-data-dir='+str(STATE/'ui')]);threading.Thread(target=lambda:drain(app.stdout),daemon=True).start()
  while app.poll() is None:
   if adapter.poll() is not None:raise RuntimeError('Session adapter stopped')
   errors=check(critical_only=True)
   if errors:raise RuntimeError('Admission monitor blocked this owned session')
   time.sleep(3)
  return app.poll()
 finally:
  for child in reversed(children):
   # Closing the anonymous job stops only this newly created process family.
   child.close()
if __name__=='__main__':
 try:sys.exit(main())
 except Exception as exc:print(type(exc).__name__+': '+str(exc),file=sys.stderr);sys.exit(1)
