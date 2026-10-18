"""Validate every ZIP member before extracting PDFs. Never executes archive contents."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import zipfile
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]

def inspect(archive: Path, output: Path):
    with zipfile.ZipFile(archive) as z:
        entries = z.infolist()
        if len(entries) > 250 or sum(x.file_size for x in entries) > 200_000_000:
            raise ValueError('Archive exceeds the inspection limits')
        seen = set()
        for item in entries:
            name = item.filename
            path = PurePosixPath(name)
            if (path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name
                or not re.fullmatch(r'[A-Za-z0-9_(). -]+\.pdf', name, re.I)
                or stat.S_ISLNK(item.external_attr >> 16) or item.flag_bits & 1
                or item.file_size > 15_000_000 or item.file_size / max(item.compress_size, 1) > 100
                or name.lower() in seen):
                raise ValueError(f'Unsafe or unsupported ZIP member: {name}')
            seen.add(name.lower())
        if z.testzip() is not None:
            raise ValueError('ZIP integrity failure')
        # All names, sizes, CRCs and types are checked before any extraction.
        pdf_dir = output / 'datasheets'
        text_dir = output / 'extracted'
        pdf_dir.mkdir(parents=True, exist_ok=True)
        text_dir.mkdir(parents=True, exist_ok=True)
        records = []
        for item in entries:
            raw = z.read(item)
            if not raw.startswith(b'%PDF-'):
                raise ValueError(f'Not a PDF: {item.filename}')
            reader = PdfReader(io.BytesIO(raw))
            if reader.is_encrypted and not reader.decrypt(''):
                raise ValueError(f'PDF requires a password: {item.filename}')
            if len(reader.pages) > 50:
                raise ValueError(f'Unsupported PDF: {item.filename}')
            pages = [page.extract_text() or '' for page in reader.pages]
            (pdf_dir / item.filename).write_bytes(raw)
            (text_dir / (item.filename + '.txt')).write_text(
                '\n'.join(f'--- PAGE {i+1} ---\n{text}' for i, text in enumerate(pages)), encoding='utf-8')
            records.append({'filename': item.filename, 'sha256': hashlib.sha256(raw).hexdigest(),
                            'bytes': len(raw), 'pages': len(pages),
                            'extracted_characters': sum(map(len, pages)), 'catalogue_review': 'pending'})
    manifest = {'archive_filename': archive.name,
                'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
                'pdf_count': len(records), 'files': records}
    (output / 'archive_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(f'Validated and inspected {len(records)} PDFs. No catalogue facts were automatically approved.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('archive', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'data')
    args = parser.parse_args()
    inspect(args.archive, args.output)
