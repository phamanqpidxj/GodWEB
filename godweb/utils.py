import os
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
