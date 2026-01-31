# Wedding Photo Gallery - Deployment Guide

## Overview
This is a two-step process:
1. **Process photos once** (locally) - Run face recognition to organize photos
2. **Deploy gallery app** - Simple Flask app that serves pre-processed photos

## Step 1: Process Photos (Run Once Locally)

```bash
# Make sure you're in the venv
source venv/bin/activate

# Process all photos (this will take time for large collections)
python process_photos.py
```

This will:
- Scan all photos in `photos_source/`
- Detect faces and group by person
- Save organized photos to `static/organized_photos/`

**For large collections (1000+ photos):**
- Processing may take 1-2 hours
- Uses ~2GB RAM
- Creates organized folders: Person_1, Person_2, etc.

## Step 2: Deploy Gallery App

### Local Testing
```bash
python gallery_app.py
```
Visit: `http://localhost:5000`

### Production Deployment

#### Option A: Simple Server (VPS/EC2)
```bash
# Install dependencies
pip install -r requirements-simple.txt

# Run with gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 gallery_app:app
```

#### Option B: Docker
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements-simple.txt .
RUN pip install -r requirements-simple.txt
COPY gallery_app.py .
COPY templates/ templates/
COPY static/ static/
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "gallery_app:app"]
```

#### Option C: Vercel/Netlify (Static Export)
For truly static hosting, you can pre-generate HTML pages.

### Performance Considerations

**For 1000+ photos:**
- Use CDN for static files (Cloudflare, AWS CloudFront)
- Enable gzip compression
- Implement lazy loading (already included)
- Consider generating thumbnails:
  ```bash
  # Add thumbnail generation to process_photos.py
  from PIL import Image
  img.thumbnail((300, 300))
  ```

**Estimated Sizes:**
- 1000 photos @ 5MB each = ~5GB storage
- With thumbnails: +500MB
- Bandwidth: ~50GB/month for 100 daily visitors

### Nginx Configuration (Production)
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
    }
    
    location /static/ {
        alias /path/to/app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

## Security Notes

- No authentication included (add if needed)
- Photos are publicly accessible
- Consider adding password protection:
  ```python
  from flask_httpauth import HTTPBasicAuth
  ```

## Scaling

**For very large collections (5000+ photos):**
1. Generate thumbnails during processing
2. Use object storage (S3, Google Cloud Storage)
3. Implement pagination in gallery
4. Add search/filter functionality
5. Consider using a database for metadata

## Cost Estimates

**AWS EC2 t3.small:**
- Instance: $15/month
- Storage (100GB): $10/month
- Bandwidth: $9/month (100GB)
**Total: ~$35/month**

**Vercel/Netlify (if static):**
- Free tier: 100GB bandwidth
- Pro: $20/month for 1TB

## Maintenance

- Photos are static after processing
- No database needed
- Minimal server resources
- Can run on shared hosting
