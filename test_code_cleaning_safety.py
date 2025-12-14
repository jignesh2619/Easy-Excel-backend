"""
Test script to verify code cleaning doesn't break valid code patterns
"""
import re

def _clean_code(python_code: str) -> str:
    """Test version of _clean_code"""
    code = python_code.strip()
    
    # Remove markdown code blocks
    if code.startswith('```'):
        lines = code.split('\n')
        if lines[0].startswith('```'):
            lines = lines[1:]
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        code = '\n'.join(lines)
    
    code = re.sub(r'```[a-z]*\n?', '', code)
    
    # Fix common syntax errors
    code = re.sub(r'\bfor_in\b', 'for _ in', code)
    code = re.sub(r'\bforin\b', 'for _ in', code)
    code = re.sub(r'\bfori\b', 'for i', code)
    code = re.sub(r'\bforj\b', 'for j', code)
    code = re.sub(r'\bforidx\b', 'for idx', code)
    
    # Fix malformed loops
    def fix_malformed_loop(match):
        statement = match.group(1).strip()
        var = match.group(2)
        range_expr = match.group(3)
        return f'for {var} in {range_expr}:\n    {statement}'
    
    pattern1 = r'(\w+\s*=\s*[^)]+\))\s+for\s+(\w+)\s+in\s+(range\([^)]+\))'
    code = re.sub(pattern1, fix_malformed_loop, code)
    
    pattern2 = r'(\w+\s*=\s*[^)]+\)(?:\.[^)]+\))+)\s+for\s+(\w+)\s+in\s+(range\([^)]+\))'
    code = re.sub(pattern2, fix_malformed_loop, code)
    
    pattern3 = r'^(\w+\s*=\s*.+\)(?:\.\w+\([^)]*\))*)\s+for\s+(\w+)\s+in\s+(range\([^)]+\))$'
    def fix_complex_loop(match):
        statement = match.group(1).strip()
        var = match.group(2)
        range_expr = match.group(3)
        return f'for {var} in {range_expr}:\n    {statement}'
    
    lines = code.split('\n')
    fixed_lines = []
    for line in lines:
        line_stripped = line.strip()
        match_obj = re.match(pattern3, line_stripped)
        if match_obj:
            statement = match_obj.group(1).strip()
            var = match_obj.group(2)
            range_expr = match_obj.group(3)
            fixed_lines.append(f'for {var} in {range_expr}:')
            fixed_lines.append(f'    {statement}')
        else:
            fixed_lines.append(line)
    code = '\n'.join(fixed_lines)
    
    return code.strip()

# Test cases - valid code that should NOT be modified
valid_codes = [
    # Valid list comprehension
    "df['New'] = [x * 2 for x in df['Old']]",
    
    # Valid for loop
    """for i in range(10):
    df = df.append({'col': i}, ignore_index=True)""",
    
    # Valid method chaining
    "df = df.dropna().reset_index(drop=True)",
    
    # Valid assignment with list comprehension
    "result = [x for x in range(10)]",
    
    # Valid generator expression
    "result = (x * 2 for x in range(10))",
    
    # Valid nested list comprehension
    "df['New'] = [[x, y] for x in range(5) for y in range(5)]",
    
    # Valid apply with lambda
    "df['New'] = df['Old'].apply(lambda x: x * 2)",
    
    # Valid conditional
    "df['Status'] = df['Value'].apply(lambda x: 'High' if x > 100 else 'Low')",
    
    # Valid drop duplicates
    "df = df.drop_duplicates().reset_index(drop=True)",
    
    # Valid concat
    "df = pd.concat([df1, df2], ignore_index=True)",
]

# Test cases - invalid code that SHOULD be fixed
invalid_codes = [
    # Malformed loop (should be fixed)
    "df = pd.concat([df.iloc[:i], pd.DataFrame([{}]), df.iloc[i:]]).reset_index(drop=True) for i in range(len(df), 0, -1)",
    
    # for_in error (should be fixed)
    "df['New'] = [x for_in range(10)]",
]

print("Testing valid code (should remain unchanged):")
print("=" * 60)
for i, code in enumerate(valid_codes, 1):
    cleaned = _clean_code(code)
    changed = cleaned != code
    status = "❌ CHANGED" if changed else "✅ OK"
    print(f"\nTest {i}: {status}")
    print(f"Original: {code[:80]}...")
    if changed:
        print(f"Cleaned:  {cleaned[:80]}...")
        print("⚠️ WARNING: Valid code was modified!")

print("\n\nTesting invalid code (should be fixed):")
print("=" * 60)
for i, code in enumerate(invalid_codes, 1):
    cleaned = _clean_code(code)
    changed = cleaned != code
    status = "✅ FIXED" if changed else "❌ NOT FIXED"
    print(f"\nTest {i}: {status}")
    print(f"Original: {code[:80]}...")
    print(f"Cleaned:  {cleaned[:200]}...")


