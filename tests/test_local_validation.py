import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('validation', Path(__file__).parents[1] / 'scripts/validate_local.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class LocalValidationTests(unittest.TestCase):
    def test_test_results_require_execution_without_failures_or_skips(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / 'results.trx'
            for values in [('0','0','0','0','0'), ('2','2','1','1','0'), ('2','1','1','0','1')]:
                attributes = ' '.join(f'{k}="{v}"' for k,v in zip(('total','executed','passed','failed','notExecuted'),values))
                file.write_text(f'<TestRun><Counters {attributes}/></TestRun>')
                with self.assertRaises(ValueError): module.counts(file)
            file.write_text('<TestRun><Counters total="2" executed="2" passed="2" failed="0" notExecuted="0"/></TestRun>')
            self.assertEqual(module.counts(file)['passed'], 2)

    def test_failed_stale_missing_and_modified_reports_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / 'config.json'
            config.write_text(json.dumps({'steps':[{'name':'build'}]}))
            log = root / 'build.log';log.write_text('passed')
            report = {'status':'passed','revision':'abc','tree':'tree','steps':[{'name':'build','exitCode':0}],'artifacts':{'build.log':module.digest(log)}}
            file = root / 'report.json'
            with patch.object(module, 'CONFIG', config), patch.object(module, 'revision', return_value=('abc','tree')):
                file.write_text(json.dumps(report));module.verify(file)
                for key,value in [('status','failed'),('revision','other'),('tree','other'),('steps',[]),('artifacts',{})]:
                    bad=dict(report);bad[key]=value;file.write_text(json.dumps(bad))
                    with self.assertRaises(ValueError):module.verify(file)
                file.write_text(json.dumps(report));log.write_text('changed')
                with self.assertRaises(ValueError):module.verify(file)

    def test_isolated_services_use_loopback_dynamic_ports_and_substitute_only_test_environment(self):
        service={'name':'redis','image':'redis:7-alpine','port':6379,'ready':['redis-cli','ping']}
        env={};owned=[]
        with patch.object(module.subprocess,'run') as run, patch.object(module,'capture',return_value='127.0.0.1:49152'):
            run.return_value.returncode=0
            module.start_services({'services':[service],'env':{'TEST_REDIS':'127.0.0.1:${LOCAL_SERVICE_REDIS_PORT}'}},env,owned)
            self.assertEqual(env['TEST_REDIS'],'127.0.0.1:49152')
            self.assertEqual(len(owned),1)
            self.assertIn('127.0.0.1::6379',run.call_args_list[0].args[0])
            self.assertTrue(owned[0].startswith('local-validation-'))

    def test_service_startup_failure_preserves_cleanup_ownership(self):
        service={'name':'redis','image':'redis:7-alpine','port':6379,'ready':['redis-cli','ping']}
        owned=[]
        with patch.object(module.subprocess,'run',side_effect=OSError('cannot start')):
            with self.assertRaises(OSError):module.start_services({'services':[service]}, {}, owned)
        self.assertEqual(len(owned),1)

    def test_image_revision_and_architecture_are_checked(self):
        base={'Os':'linux','Architecture':'amd64','Config':{'Labels':{'org.opencontainers.image.revision':'abc'}},'RootFS':{'Layers':['sha256:example']}}
        with patch.object(module,'capture',return_value=json.dumps([base])):
            self.assertTrue(module.image_fingerprint('image','abc'))
            with self.assertRaises(ValueError):module.image_fingerprint('image','other')
        base['Architecture']='arm64'
        with patch.object(module,'capture',return_value=json.dumps([base])):
            with self.assertRaises(ValueError):module.image_fingerprint('image','abc')


if __name__ == '__main__': unittest.main()
