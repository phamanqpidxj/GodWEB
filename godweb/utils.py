import os
import shutil
import zipfile
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

# Check if Cloudinary is configured
CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL')

if CLOUDINARY_URL:
    import cloudinary
    import cloudinary.uploader
    # Cloudinary is auto-configured from CLOUDINARY_URL environment variable
    cloudinary.config(secure=True)

def upload_image(file, folder='godweb'):
    """
    Upload image to Cloudinary if configured, otherwise save locally.
    Returns the URL or filename of the uploaded image.
    """
    if not file:
        return None

    # Get original filename or generate one for pasted images
    original_filename = file.filename if file.filename else 'image.png'

    # Get file extension
    if '.' in original_filename:
        ext = original_filename.rsplit('.', 1)[-1].lower()
    else:
        ext = 'png'

    # Validate extension
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}
    if ext not in allowed_extensions:
        ext = 'png'

    # Generate unique filename
    unique_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.{ext}"

    if CLOUDINARY_URL:
        # Upload to Cloudinary
        try:
            result = cloudinary.uploader.upload(
                file,
                folder=folder,
                resource_type='image',
                public_id=unique_name.rsplit('.', 1)[0]
            )
            return result.get('secure_url')
        except Exception as e:
            print(f"Cloudinary upload error: {e}")
            return None
    else:
        # Save locally for development
        from flask import current_app

        upload_folder = current_app.config['UPLOAD_FOLDER']

        # Ensure upload folder exists
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        filepath = os.path.join(upload_folder, unique_name)

        try:
            file.save(filepath)
            return unique_name
        except Exception as e:
            print(f"Local upload error: {e}")
            return None

def get_image_url(image_path):
    """
    Get the URL for an image.
    If it's a Cloudinary URL, return as-is.
    If it's a local filename, generate the local URL.
    """
    if not image_path:
        return None

    # If it's already a full URL (Cloudinary), return as-is
    if image_path.startswith('http://') or image_path.startswith('https://'):
        return image_path

    # Otherwise, it's a local filename
    from flask import url_for
    return url_for('main.uploaded_file', filename=image_path)

def is_cloudinary_url(url):
    """Check if URL is from Cloudinary"""
    return url and ('cloudinary.com' in url or 'res.cloudinary.com' in url)


def normalize_inventory_parse_mode(mode):
    """Return a safe parse mode value for inventory files."""
    return 'separator' if mode == 'separator' else 'line'


def _trim_empty_edges(lines):
    """Remove empty lines at block edges while preserving internal formatting."""
    start = 0
    end = len(lines)

    while start < end and not lines[start].strip():
        start += 1
    while end > start and not lines[end - 1].strip():
        end -= 1

    return lines[start:end]


def parse_inventory_accounts_text(content, parse_mode='line'):
    """Parse inventory accounts from a raw string.

    Used when inventory is stored in DB (preferred) instead of on disk.
    """
    mode = normalize_inventory_parse_mode(parse_mode)
    raw = content or ''

    if mode == 'line':
        return [line.strip() for line in raw.splitlines() if line.strip()]

    accounts = []
    current_block = []

    for line in raw.splitlines():
        if line.strip() == '|':
            block_lines = _trim_empty_edges(current_block)
            if block_lines:
                accounts.append('\n'.join(block_lines))
            current_block = []
            continue
        current_block.append(line)

    block_lines = _trim_empty_edges(current_block)
    if block_lines:
        accounts.append('\n'.join(block_lines))

    return accounts


def serialize_inventory_accounts(accounts, parse_mode='line'):
    """Inverse of parse_inventory_accounts_text: rebuild raw string for storage."""
    mode = normalize_inventory_parse_mode(parse_mode)
    if mode == 'separator':
        return '\n|\n'.join(accounts)
    return '\n'.join(accounts)


def parse_zip_to_accounts(uploaded_file):
    """Parse a .zip into list of (filename, content) tuples for DB storage.

    Mirrors extract_inventory_zip but never writes to disk; returned filenames
    are sanitized and de-duplicated. Raises ValueError on invalid input.
    """
    try:
        archive = zipfile.ZipFile(uploaded_file)
    except zipfile.BadZipFile as exc:
        raise ValueError('File upload không phải zip hợp lệ') from exc

    accounts = []
    used_names = set()
    with archive:
        for item in archive.infolist():
            if item.is_dir():
                continue
            raw_name = item.filename.replace('\\', '/')
            normalized_parts = [part for part in raw_name.split('/') if part and part != '.']
            if not normalized_parts or '..' in normalized_parts:
                continue
            original_name = normalized_parts[-1]
            if not original_name.lower().endswith('.txt'):
                continue
            safe_name = secure_filename(original_name)
            if not safe_name:
                continue
            base, ext = os.path.splitext(safe_name)
            candidate = safe_name
            suffix = 1
            while candidate.lower() in used_names:
                candidate = f"{base}_{suffix}{ext}"
                suffix += 1
            file_text = archive.read(item).decode('utf-8-sig', errors='replace').strip()
            if not file_text:
                continue
            used_names.add(candidate.lower())
            accounts.append((candidate, file_text))

    if not accounts:
        raise ValueError('File zip không chứa tài khoản .txt hợp lệ')
    return accounts


def parse_inventory_accounts(filepath, parse_mode='line'):
    """Parse inventory accounts from text file by selected mode."""
    mode = normalize_inventory_parse_mode(parse_mode)

    with open(filepath, 'r', encoding='utf-8') as f:
        raw = f.read()

    if mode == 'line':
        return [line.strip() for line in raw.splitlines() if line.strip()]

    accounts = []
    current_block = []

    for line in raw.splitlines():
        if line.strip() == '|':
            block_lines = _trim_empty_edges(current_block)
            if block_lines:
                accounts.append('\n'.join(block_lines))
            current_block = []
            continue
        current_block.append(line)

    block_lines = _trim_empty_edges(current_block)
    if block_lines:
        accounts.append('\n'.join(block_lines))

    return accounts


def write_inventory_accounts(filepath, accounts, parse_mode='line'):
    """Write accounts back to inventory file in the selected mode."""
    mode = normalize_inventory_parse_mode(parse_mode)

    if mode == 'separator':
        content = '\n|\n'.join(accounts)
    else:
        content = '\n'.join(accounts)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)


def cleanup_inventory_folder(upload_folder, folder_name):
    """Delete a product inventory folder if it exists."""
    if not folder_name:
        return

    folder_path = os.path.join(upload_folder, folder_name)
    if os.path.isdir(folder_path):
        shutil.rmtree(folder_path, ignore_errors=True)


def list_inventory_folder_files(folder_path):
    """Return sorted .txt files from inventory folder (A-Z, case-insensitive)."""
    if not folder_path or not os.path.isdir(folder_path):
        return []

    files = []
    for name in os.listdir(folder_path):
        path = os.path.join(folder_path, name)
        if os.path.isfile(path) and name.lower().endswith('.txt'):
            files.append(name)

    return sorted(files, key=lambda item: item.lower())


def read_inventory_folder_account(folder_path, filename):
    """Read one account file content from folder inventory mode."""
    account_path = os.path.join(folder_path, filename)
    with open(account_path, 'r', encoding='utf-8') as f:
        return f.read().strip()


def consume_inventory_folder_account(folder_path, filename):
    """Delete a consumed account file from folder inventory mode."""
    account_path = os.path.join(folder_path, filename)
    if os.path.exists(account_path):
        os.remove(account_path)


def extract_inventory_zip(uploaded_file, upload_folder, product_id):
    """
    Extract a zip containing .txt account files into a per-product folder.
    Returns (folder_name, files_count).
    """
    folder_name = f"inventory_folder_{product_id}"
    target_folder = os.path.join(upload_folder, folder_name)

    cleanup_inventory_folder(upload_folder, folder_name)
    os.makedirs(target_folder, exist_ok=True)

    try:
        with zipfile.ZipFile(uploaded_file) as archive:
            used_names = set()
            txt_count = 0

            for item in archive.infolist():
                if item.is_dir():
                    continue

                raw_name = item.filename.replace('\\', '/')
                normalized_parts = [part for part in raw_name.split('/') if part and part != '.']

                # Prevent zip-slip and unsupported paths.
                if not normalized_parts or '..' in normalized_parts:
                    continue

                original_name = normalized_parts[-1]
                if not original_name.lower().endswith('.txt'):
                    continue

                safe_name = secure_filename(original_name)
                if not safe_name:
                    continue

                base, ext = os.path.splitext(safe_name)
                candidate = safe_name
                suffix = 1
                while candidate.lower() in used_names:
                    candidate = f"{base}_{suffix}{ext}"
                    suffix += 1

                file_bytes = archive.read(item)
                file_text = file_bytes.decode('utf-8-sig', errors='replace').strip()
                if not file_text:
                    continue

                destination = os.path.join(target_folder, candidate)
                with open(destination, 'w', encoding='utf-8') as f:
                    f.write(file_text)

                used_names.add(candidate.lower())
                txt_count += 1

        if txt_count == 0:
            cleanup_inventory_folder(upload_folder, folder_name)
            raise ValueError('File zip không chứa tài khoản .txt hợp lệ')

        return folder_name, txt_count
    except zipfile.BadZipFile as exc:
        cleanup_inventory_folder(upload_folder, folder_name)
        raise ValueError('File upload không phải zip hợp lệ') from exc
    except Exception:
        cleanup_inventory_folder(upload_folder, folder_name)
        raise
