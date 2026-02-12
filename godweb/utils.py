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
