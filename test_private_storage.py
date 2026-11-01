"""Synthetic storage tests only; not an enclave or encryption proof."""
import importlib.util
import json
import os
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('private_test_server',ROOT/'app/server.py')
assert spec is not None and spec.loader is not None
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)


class PrivateStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)/'private'
        self.settings=patch.object(s,'DATA',self.root);self.settings.start()
        self.old_umask=os.umask(0)

    def tearDown(self):
        os.umask(self.old_umask)
        self.settings.stop();self.temp.cleanup()

    def test_create_replace_legacy_restart_and_cache_modes(self):
        s.initialize()
        key='SYNTHETIC-KEY-NOT-A-CREDENTIAL'
        s.atomic('connection.json',{'key':key,'authenticated':True,'models':['synthetic'],'verifiedAt':'synthetic'})
        s.atomic('admin.json',{'key':key})
        cache=self.root/'.tinfoil';cache.mkdir()
        (cache/'user_cache_secret').write_bytes(b'synthetic-cache')
        # Simulate externally widened legacy storage, then a restart migration (metadata only).
        paths=[self.root,cache,*self.root.glob('*.json'),cache/'user_cache_secret']
        before={str(p.relative_to(self.root)):p.read_bytes() for p in paths if p.is_file()}
        for p in paths:p.chmod(0o777)
        s.initialize()
        self.assertEqual(before,{str(p.relative_to(self.root)):p.read_bytes() for p in paths if p.is_file()})
        for p in paths:self.assertEqual(p.stat().st_mode&0o777,0o700 if p.is_dir() else 0o600)
        self.assertNotIn(key,json.dumps(s.status()))
        s.atomic('connection.json',{'key':key,'models':[],'verifiedAt':'new'})
        self.assertEqual((self.root/'connection.json').stat().st_mode&0o777,0o600)

    def test_failure_preserves_original_and_no_pending_file(self):
        s.initialize();s.atomic('connection.json',{'key':'synthetic-original'})
        before=(self.root/'connection.json').read_bytes()
        with patch.object(s.os,'replace',side_effect=OSError('synthetic disk failure')):
            with self.assertRaises(OSError):s.atomic('connection.json',{'key':'synthetic-new'})
        self.assertEqual(before,(self.root/'connection.json').read_bytes())
        self.assertFalse(list(self.root.glob('.pending-*')))

    def test_worker_always_uses_private_child_umask_and_repairs_after_failure(self):
        s.initialize();s.atomic('connection.json',{'key':'synthetic'})
        with patch.object(s.subprocess,'run',side_effect=ValueError('synthetic')) as run:
            with self.assertRaises(ValueError):s.worker('verify','synthetic')
        self.assertEqual(run.call_args.kwargs['umask'],0o077)
        self.assertEqual(self.root.stat().st_mode&0o777,0o700)
        self.assertEqual((self.root/'connection.json').stat().st_mode&0o777,0o600)

    def test_symlink_rejected(self):
        s.initialize()
        outside=Path(self.temp.name)/'outside';outside.write_bytes(b'synthetic');outside.chmod(0o644)
        (self.root/'connection.json').symlink_to(outside)
        with self.assertRaisesRegex(ValueError,'^Private storage unavailable.$'):s.harden_storage()
        self.assertEqual(outside.stat().st_mode&0o777,0o644)

    def test_real_child_create_cache_and_sanitized_log(self):
        s.initialize()
        fake=Path(self.temp.name)/'fake';(fake/'app').mkdir(parents=True)
        (fake/'app/provider.py').write_text("from pathlib import Path\nimport os\np=Path(os.environ['SYNTHETIC_DATA'])/'.tinfoil';p.mkdir(exist_ok=True);(p/'user_cache_secret').write_bytes(b'synthetic')\nprint('{}')\n")
        with patch.object(s,'ROOT',fake),patch.dict(os.environ,{'SYNTHETIC_DATA':str(self.root)}):
            self.assertEqual(s.worker('verify','synthetic'),{})
        self.assertEqual((self.root/'.tinfoil').stat().st_mode&0o777,0o700)
        self.assertEqual((self.root/'.tinfoil/user_cache_secret').stat().st_mode&0o777,0o600)
        out=io.StringIO()
        with contextlib.redirect_stderr(out):
            try:raise RuntimeError('SYNTHETIC-DO-NOT-EXPOSE')
            except RuntimeError:s.Server.handle_error(None,None,None)
        self.assertNotIn('SYNTHETIC-DO-NOT-EXPOSE',out.getvalue())


if __name__=='__main__':unittest.main()
