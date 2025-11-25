"""
Quick script to remove quotes from .env file values
"""
import re
from pathlib import Path

env_path = Path(__file__).parent / ".env"

if not env_path.exists():
    print("❌ .env file not found!")
    exit(1)

# Read the file
with open(env_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove quotes from values (handles both single and double quotes)
# Pattern: KEY='value' or KEY="value" -> KEY=value
lines = content.split('\n')
fixed_lines = []

for line in lines:
    if '=' in line and not line.strip().startswith('#'):
        # Split into key and value
        parts = line.split('=', 1)
        if len(parts) == 2:
            key = parts[0].strip()
            value = parts[1].strip()
            
            # Remove surrounding quotes
            if (value.startswith("'") and value.endswith("'")) or \
               (value.startswith('"') and value.endswith('"')):
                value = value[1:-1]
            
            fixed_lines.append(f"{key}={value}")
        else:
            fixed_lines.append(line)
    else:
        fixed_lines.append(line)

# Write back
with open(env_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(fixed_lines))

print("✅ Fixed .env file - removed quotes from values")
print("Please restart your server for changes to take effect.")

