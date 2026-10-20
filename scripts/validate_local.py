#!/usr/bin/env python3
"""Execute repository-specific local checks and verify exact-commit evidence."""
import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import time
import uuid
from string import Template
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'scripts/local-validation.json'


def capture(args):
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def revision():
    if capture(['git', 'status', '--porcelain']):
        raise ValueError('Validation requires a clean working tree.')
    return capture(['git', 'rev-parse', 'HEAD']), capture(['git', 'rev-parse', 'HEAD^{tree}'])


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def counts(path):
    result = ET.parse(path).find('.//{*}Counters')
    if result is None:
        raise ValueError('Missing test counters.')
    c = {k: int(result.get(k, '0')) for k in ('total', 'executed', 'passed', 'failed', 'notExecuted')}
    if not c['total'] or c['total'] != c['passed'] or c['total'] != c['executed'] or c['failed'] or c['notExecuted']:
        raise ValueError('Failed, empty or skipped test run: ' + str(c))
    return c


def image_fingerprint(image, sha):
    item = json.loads(capture(['docker', 'image', 'inspect', image]))[0]
    if item['Os'] != 'linux' or item['Architecture'] != 'amd64':
        raise ValueError('Image must be linux/amd64.')
    if item['Config'].get('Labels', {}).get('org.opencontainers.image.revision') != sha:
        raise ValueError('Image revision differs from the checked commit.')
    return hashlib.sha256(json.dumps({k: item[k] for k in ('Os', 'Architecture', 'Config', 'RootFS')}, sort_keys=True).encode()).hexdigest()


def verify(path):
    sha, tree = revision()
    path = Path(path).resolve()
    report = json.loads(path.read_text())
    config = json.loads(CONFIG.read_text())
    if report.get('status') != 'passed' or report.get('revision') != sha or report.get('tree') != tree:
        raise ValueError('Report is failed, incomplete or belongs to another revision.')
    expected = [s['name'] for s in config['steps']]
    if [s['name'] for s in report.get('steps', [])] != expected or any(s.get('exitCode') != 0 for s in report['steps']):
        raise ValueError('Required checks are missing or failed.')
    required = {s + '.log' for s in expected} | set(report.get('tests', {}))
    if not required.issubset(report.get('artifacts', {})):
        raise ValueError('Missing required artifacts.')
    for name, hash_value in report['artifacts'].items():
        file = (path.parent / name).resolve()
        if not file.is_relative_to(path.parent) or digest(file) != hash_value:
            raise ValueError('Missing or altered artifact: ' + name)
    for name, recorded in report.get('tests', {}).items():
        if counts(path.parent / name) != recorded:
            raise ValueError('Test counters changed.')
    if config.get('dotnetTests') and not report.get('tests'):
        raise ValueError('Missing .NET test evidence.')
    for image, fingerprint in report.get('images', {}).items():
        if image_fingerprint(image, sha) != fingerprint:
            raise ValueError('Validated image changed.')
    if config.get('image') and list(report.get('images', {})) != [config['image'] + ':local-' + sha[:12]]:
        raise ValueError('Missing expected image evidence.')
    return report


def start_services(config, env, owned):
    for service in config.get('services', []):
        name = 'local-validation-' + uuid.uuid4().hex[:16]
        port = service['port']
        command = ['docker', 'run', '--detach', '--name', name, '--publish', f'127.0.0.1::{port}']
        for key, value in service.get('env', {}).items():
            command += ['--env', key + '=' + value]
        command.append(service['image'])
        # Register before launch so even an interrupted startup has a cleanup owner.
        owned.append(name)
        subprocess.run(command, cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
        address = capture(['docker', 'port', name, str(port) + '/tcp'])
        env['LOCAL_SERVICE_' + service['name'].upper() + '_PORT'] = address.rsplit(':', 1)[1]
        for _ in range(60):
            result = subprocess.run(['docker', 'exec', name, *service['ready']], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if result.returncode == 0:
                break
            time.sleep(1)
        else:
            raise ValueError('Isolated test service failed readiness: ' + service['name'])
    for key, value in config.get('env', {}).items():
        env[key] = Template(value).substitute(env)


def run():
    sha, tree = revision()
    config = json.loads(CONFIG.read_text())
    output = ROOT / 'artifacts/local-validation' / sha
    output.mkdir(parents=True, exist_ok=True)
    # Only this runner-owned commit directory may contain prior test results.
    shutil.rmtree(output / 'test-results', ignore_errors=True)
    report = {'schemaVersion': 1, 'revision': sha, 'tree': tree, 'status': 'running', 'steps': [], 'artifacts': {}, 'tests': {}, 'images': {}}
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    if config.get('nodeMajor'):
        candidate = env.get('NODE22_BIN', '/opt/homebrew/opt/node@22/bin')
        if Path(candidate, 'node').is_file():
            env['PATH'] = candidate + os.pathsep + env['PATH']
        version = subprocess.check_output(['node', '--version'], env=env, text=True).strip()
        if not version.startswith('v' + str(config['nodeMajor']) + '.'):
            raise ValueError('Required Node major: ' + str(config['nodeMajor']))
    env.update({'LOCAL_VALIDATION_OUTPUT': str(output), 'LOCAL_VALIDATION_REVISION': sha, 'LOCAL_VALIDATION_IMAGE': config.get('image', 'local') + ':local-' + sha[:12]})
    if config.get('privateNuget') and not env.get('NuGetPackageSourceCredentials_advancersoft'):
        package_access = env.get('NUGET_AUTH_TOKEN') or capture(['gh', 'auth', 'token'])
        user = env.get('NUGET_USER') or capture(['gh', 'api', 'user', '--jq', '.login'])
        env['NuGetPackageSourceCredentials_advancersoft'] = f'Username={user};Password={package_access};ValidAuthenticationTypes=Basic'
    env['NUGET_CREDENTIALS'] = env.get('NuGetPackageSourceCredentials_advancersoft', '')
    report_path = output / 'report.json'
    owned = []
    try:
        start_services(config, env, owned)
        for step in config['steps']:
            print('Checking ' + step['name'] + '...', flush=True)
            log = output / (step['name'] + '.log')
            start = time.monotonic()
            with log.open('w') as handle:
                result = subprocess.run(step['command'], cwd=ROOT, env=env, stdout=handle, stderr=subprocess.STDOUT)
            report['steps'].append({'name': step['name'], 'exitCode': result.returncode, 'seconds': round(time.monotonic()-start, 3)})
            report['artifacts'][log.name] = digest(log)
            if result.returncode:
                raise ValueError('Check failed: ' + step['name'] + '; see ' + str(log))
        if config.get('dotnetTests'):
            files = sorted((output / 'test-results').rglob('*.trx'))
            if not files:
                raise ValueError('No .NET test results were produced.')
            for file in files:
                name = str(file.relative_to(output))
                report['tests'][name] = counts(file)
                report['artifacts'][name] = digest(file)
        if config.get('image'):
            image = env['LOCAL_VALIDATION_IMAGE']
            report['images'][image] = image_fingerprint(image, sha)
        if revision() != (sha, tree):
            raise ValueError('Source changed during validation.')
        report['status'] = 'passed'
    except BaseException as error:
        report['status'] = 'failed'
        report['error'] = str(error)
        raise
    finally:
        report_path.write_text(json.dumps(report, indent=2) + '\n')
        for name in reversed(owned):
            subprocess.run(['docker', 'rm', '--force', name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    verify(report_path)
    print('Validation passed: ' + str(report_path))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['run', 'verify'])
    parser.add_argument('report', nargs='?')
    args = parser.parse_args()
    try:
        if args.action == 'run':
            run()
        elif args.report:
            result = verify(args.report)
            print('\n'.join(result['images']) or 'Validation verified.')
        else:
            parser.error('verify requires a report path')
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
