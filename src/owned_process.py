"""Anonymous Windows job: only newly created children, atomically assigned, no breakaway."""
import ctypes,io,msvcrt,os,subprocess
from ctypes import wintypes as w
K=ctypes.WinDLL('kernel32',use_last_error=True)
SIZE=ctypes.c_size_t;PTR=ctypes.c_void_p
class SA(ctypes.Structure):_fields_=[('length',w.DWORD),('descriptor',PTR),('inherit',w.BOOL)]
class START(ctypes.Structure):
 _fields_=[('cb',w.DWORD),('reserved',w.LPWSTR),('desktop',w.LPWSTR),('title',w.LPWSTR),('x',w.DWORD),('y',w.DWORD),('width',w.DWORD),('height',w.DWORD),('xchars',w.DWORD),('ychars',w.DWORD),('fill',w.DWORD),('flags',w.DWORD),('show',w.WORD),('reserved2_size',w.WORD),('reserved2',PTR),('stdin',w.HANDLE),('stdout',w.HANDLE),('stderr',w.HANDLE)]
class STARTEX(ctypes.Structure):_fields_=[('start',START),('attributes',PTR)]
class PI(ctypes.Structure):_fields_=[('process',w.HANDLE),('thread',w.HANDLE),('pid',w.DWORD),('tid',w.DWORD)]
class LIMIT(ctypes.Structure):_fields_=[('process_time',ctypes.c_longlong),('job_time',ctypes.c_longlong),('flags',w.DWORD),('min_ws',SIZE),('max_ws',SIZE),('process_limit',w.DWORD),('affinity',SIZE),('priority',w.DWORD),('scheduling',w.DWORD)]
class COUNTERS(ctypes.Structure):_fields_=[(name,ctypes.c_ulonglong) for name in ('readops','writeops','otherops','readbytes','writebytes','otherbytes')]
class EXT_LIMIT(ctypes.Structure):_fields_=[('basic',LIMIT),('io',COUNTERS),('process_memory',SIZE),('job_memory',SIZE),('peak_process',SIZE),('peak_job',SIZE)]
K.CreateJobObjectW.argtypes=[PTR,w.LPCWSTR];K.CreateJobObjectW.restype=w.HANDLE
K.SetInformationJobObject.argtypes=[w.HANDLE,ctypes.c_int,PTR,w.DWORD];K.SetInformationJobObject.restype=w.BOOL
K.CreatePipe.argtypes=[ctypes.POINTER(w.HANDLE),ctypes.POINTER(w.HANDLE),ctypes.POINTER(SA),w.DWORD];K.CreatePipe.restype=w.BOOL
K.SetHandleInformation.argtypes=[w.HANDLE,w.DWORD,w.DWORD];K.SetHandleInformation.restype=w.BOOL
K.InitializeProcThreadAttributeList.argtypes=[PTR,w.DWORD,w.DWORD,ctypes.POINTER(SIZE)];K.InitializeProcThreadAttributeList.restype=w.BOOL
K.UpdateProcThreadAttribute.argtypes=[PTR,w.DWORD,SIZE,PTR,SIZE,PTR,PTR];K.UpdateProcThreadAttribute.restype=w.BOOL
K.DeleteProcThreadAttributeList.argtypes=[PTR]
K.CreateProcessW.argtypes=[w.LPCWSTR,w.LPWSTR,PTR,PTR,w.BOOL,w.DWORD,PTR,w.LPCWSTR,PTR,ctypes.POINTER(PI)];K.CreateProcessW.restype=w.BOOL
K.CloseHandle.argtypes=[w.HANDLE];K.CloseHandle.restype=w.BOOL
K.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD];K.WaitForSingleObject.restype=w.DWORD
K.GetExitCodeProcess.argtypes=[w.HANDLE,ctypes.POINTER(w.DWORD)];K.GetExitCodeProcess.restype=w.BOOL
K.TerminateJobObject.argtypes=[w.HANDLE,w.UINT];K.TerminateJobObject.restype=w.BOOL
def check(ok):
 if not ok:raise ctypes.WinError(ctypes.get_last_error())
class OwnedProcess:
 def __init__(self,argv,cwd,env):
  self.job=K.CreateJobObjectW(None,None);check(self.job);handles=[];attribute=None
  try:
   limits=EXT_LIMIT();limits.basic.flags=0x2000;check(K.SetInformationJobObject(self.job,9,ctypes.byref(limits),ctypes.sizeof(limits)))
   sa=SA(ctypes.sizeof(SA),None,True)
   def pipe():
    read=w.HANDLE();write=w.HANDLE();check(K.CreatePipe(ctypes.byref(read),ctypes.byref(write),ctypes.byref(sa),0));handles.extend([read.value,write.value]);return read.value,write.value
   stdin_read,stdin_write=pipe();stdout_read,stdout_write=pipe();stderr_read,stderr_write=pipe()
   for handle in (stdin_write,stdout_read,stderr_read):check(K.SetHandleInformation(handle,1,0))
   needed=SIZE();K.InitializeProcThreadAttributeList(None,2,0,ctypes.byref(needed));attribute=ctypes.create_string_buffer(needed.value);check(K.InitializeProcThreadAttributeList(attribute,2,0,ctypes.byref(needed)))
   inherited=(w.HANDLE*3)(stdin_read,stdout_write,stderr_write);jobs=(w.HANDLE*1)(self.job)
   check(K.UpdateProcThreadAttribute(attribute,0,0x20002,inherited,ctypes.sizeof(inherited),None,None))
   check(K.UpdateProcThreadAttribute(attribute,0,0x2000D,jobs,ctypes.sizeof(jobs),None,None))
   start=STARTEX();start.start.cb=ctypes.sizeof(start);start.attributes=ctypes.cast(attribute,PTR);start.start.flags=0x101;start.start.show=0;start.start.stdin=stdin_read;start.start.stdout=stdout_write;start.start.stderr=stderr_write
   line=ctypes.create_unicode_buffer(subprocess.list2cmdline(argv));environment=ctypes.create_unicode_buffer('\0'.join(k+'='+str(v) for k,v in sorted(env.items(),key=lambda pair:pair[0].upper()))+'\0\0');process=PI()
   # The job is applied at creation. No CREATE_BREAKAWAY_FROM_JOB, account or privilege changes.
   check(K.CreateProcessW(None,line,None,None,True,0x08000000|0x00080000|0x00000400,environment,str(cwd),ctypes.byref(start),ctypes.byref(process)))
   self.handle=process.process;self.pid=process.pid;K.CloseHandle(process.thread)
   for handle in (stdin_read,stdout_write,stderr_write):K.CloseHandle(handle);handles.remove(handle)
   self.stdin=os.fdopen(msvcrt.open_osfhandle(stdin_write,os.O_WRONLY|os.O_BINARY),'wb',buffering=0);handles.remove(stdin_write)
   self.stdout=os.fdopen(msvcrt.open_osfhandle(stdout_read,os.O_RDONLY|os.O_BINARY),'rb',buffering=0);handles.remove(stdout_read)
   self.stderr=os.fdopen(msvcrt.open_osfhandle(stderr_read,os.O_RDONLY|os.O_BINARY),'rb',buffering=0);handles.remove(stderr_read)
  except BaseException:
   K.CloseHandle(self.job);self.job=None
   raise
  finally:
   if attribute is not None:K.DeleteProcThreadAttributeList(attribute)
   for handle in handles:K.CloseHandle(handle)
 def poll(self):
  if K.WaitForSingleObject(self.handle,0)==258:return None
  result=w.DWORD();check(K.GetExitCodeProcess(self.handle,ctypes.byref(result)));return result.value
 def wait(self,timeout=None):
  status=K.WaitForSingleObject(self.handle,0xFFFFFFFF if timeout is None else int(timeout*1000))
  if status==258:raise subprocess.TimeoutExpired('owned process',timeout)
  return self.poll()
 def terminate(self):check(K.TerminateJobObject(self.job,1))
 def close(self):
  if self.job:K.CloseHandle(self.job);self.job=None
  if getattr(self,'handle',None):K.CloseHandle(self.handle);self.handle=None
  for name in ('stdin','stdout','stderr'):
   stream=getattr(self,name,None)
   if stream:
    try:stream.close()
    except OSError:pass
