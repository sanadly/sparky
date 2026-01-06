import os
import sys
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

# Setup paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'backend', 'templates')
OUTPUT_FILE = os.path.join(BASE_DIR, 'preview_offer_email.html')

def generate_preview():
    # Setup Jinja2 environment
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    
    try:
        template = env.get_template('offer_email.html')
        
        # Sample data
        data = {
            'offer_id': 'OFF-2024-88A9',
            'product_name': 'Green Power 12',
            'consumption': '3500',
            'price': '1.249,50 €',
            'year': datetime.now().year
        }
        
        # Render template
        html_content = template.render(**data)
        
        # Write to file
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print(f"✅ Preview generated at: {OUTPUT_FILE}")
        
    except Exception as e:
        print(f"❌ Error generating preview: {e}")

if __name__ == "__main__":
    generate_preview()
