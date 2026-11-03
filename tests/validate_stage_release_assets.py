#!/usr/bin/env python3
"""Self-contained staging checks, including stale renders and immutable releases."""

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from release_archive import verify, checksum
from publication_metadata import render_provenance


def main():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        source = tmp / "source/v2099.1"
        source.mkdir(parents=True)
        (source / "checklist.csv").write_text('avibase_id,sequence,english_name,scientific_name\nexample,1,Example,Alpha beta\n')
        (source / "checklist.pdf").write_bytes(b"fixture PDF")
        for name, data in [('policy.md', 'Policy'), ('categories.csv', 'code,label\n'), ('pending.csv', 'avibase_id\n')]:
            (tmp / name).write_text(data)
        curation = tmp / "curation/earc_decisions.csv"
        curation.parent.mkdir()
        curation.write_text('avibase_id,decision\n')
        (source / "manifest.json").write_text(json.dumps({'release_id': 'v2099.1', 'sources': {'earc_decisions_path': {'path': str(curation), 'sha256': checksum(curation)}}}))
        metadata = {'release_id': 'v2099.1', 'status': 'draft', 'sources': {'policy': str(tmp / 'policy.md'), 'category_definitions': str(tmp / 'categories.csv'), 'pending_earc': str(tmp / 'pending.csv')}, 'render': {'output_filename': 'checklist.pdf'}}
        publication = tmp / 'publication.toml'
        publication.write_text('release_id = "v2099.1"\nstatus = "draft"\n[sources]\n' + '\n'.join(f'{k} = "{v}"' for k, v in metadata['sources'].items()) + '\n[render]\noutput_filename = "checklist.pdf"\n')
        provenance = render_provenance(metadata, ROOT, source, source / 'checklist.pdf')
        (source / 'checklist.inputs.json').write_text(json.dumps(provenance))
        command = [sys.executable, str(ROOT / "scripts/stage_release_assets.py"), '--publication', str(publication), "--source", str(source), "--output-root", str(tmp / "archive")]
        subprocess.run(command, check=True, capture_output=True)
        bundle = tmp / "archive/v2099.1"
        descriptor = verify(bundle)
        assert len(list(bundle.glob("*.pdf"))) == 1 and not (bundle / "comparison").exists()
        assert (bundle / "curation/earc_decisions.csv").is_file()
        original = (source / "checklist.csv").read_bytes()
        (source / "checklist.csv").write_bytes(original + b'\n')
        result = subprocess.run(command, capture_output=True, text=True)
        assert result.returncode and 'PDF is stale' in result.stderr
        (source / "checklist.csv").write_bytes(original)
        (tmp / 'policy.md').write_text('Changed policy')
        result = subprocess.run(command, capture_output=True, text=True)
        assert result.returncode and 'PDF is stale' in result.stderr
        (tmp / 'policy.md').write_text('Policy')
        (tmp / "pending.csv").write_text("avibase_id\nexample\n")
        result = subprocess.run(command, capture_output=True, text=True)
        assert result.returncode and "PDF is stale" in result.stderr
        (tmp / "pending.csv").write_text("avibase_id\n")
        descriptor["status"] = "released"
        (bundle / "release.json").write_text(json.dumps(descriptor))
        result = subprocess.run(command, capture_output=True, text=True)
        assert result.returncode and 'immutable' in result.stderr
        verify(bundle)
        (bundle / 'checklist.csv').write_text('Changed archive')
        try:
            verify(bundle)
        except ValueError as error:
            assert 'has changed' in str(error)
        else:
            raise AssertionError('archive mutation was undetected')
    print("Validated curation snapshots, one PDF, stale checklist/editorial rejection, published immutability and archive tampering")


if __name__ == "__main__":
    main()
