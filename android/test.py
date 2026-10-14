from pathlib import Path
import subprocess,os
APP=Path(__file__).resolve().parent;ROOT=APP.parent
classpath=str(APP/'vendor/json-20250107.jar')+os.pathsep+str(APP/'vendor/bcprov-jdk15to18-1.81.jar')
def run(*args):subprocess.run([str(a) for a in args],cwd=ROOT,check=True)
run('node',APP/'tests/generate-fixtures.cjs',APP/'build/test-fixtures')
run('java','--module','jdk.compiler/com.sun.tools.javac.Main','-cp',classpath,'-d',APP/'build/test-classes',APP/'build/owner/BuildConfig.java',APP/'src/in/kpmaster/mobile/LicenseManager.java',*sorted((APP/'tests/jvm').rglob('*.java')))
run('java','-cp',str(APP/'build/test-classes')+os.pathsep+classpath,'in.kpmaster.mobile.LicenseTest',APP/'build/test-fixtures')
run('python',APP/'tests/mobile_bridge.py')
