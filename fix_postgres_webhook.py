#!/usr/bin/env python3
"""
Quick fix to add DB visibility and fix any remaining Postgres issues in webhook_main.py
"""

import os

# Read webhook_main.py
with open('webhook_main.py', 'r') as f:
    content = f.read()

# Add urlparse import if not present
if 'from urllib.parse import urlparse' not in content:
    content = content.replace(
        'from contextlib import asynccontextmanager',
        'from contextlib import asynccontextmanager\nfrom urllib.parse import urlparse'
    )

# Add DB logging to startup
startup_addition = '''
    # Log DB visibility to confirm env wiring on Render
    db_url = os.getenv("DATABASE_URL", "")
    if db_url:
        try:
            parsed = urlparse(db_url)
            logger.info(
                f"[Startup] DATABASE_URL detected → scheme={parsed.scheme} host={parsed.hostname} db={parsed.path.lstrip('/')} ssl={'sslmode=' in db_url}"
            )
        except Exception as e:
            logger.info(f"[Startup] DATABASE_URL present but could not parse: {e}")
    else:
        logger.warning("[Startup] DATABASE_URL not set (will fallback to SQLite if supported)")
'''

if '[Startup] DATABASE_URL detected' not in content:
    content = content.replace(
        '    logger.info("[Startup] Shanbot Webhook starting up...")',
        '    logger.info("[Startup] Shanbot Webhook starting up...")\n' + startup_addition
    )

# Update debug endpoint
debug_update = '''        db_url = os.getenv("DATABASE_URL", "")
        db_info = {}
        if db_url:
            try:
                parsed = urlparse(db_url)
                db_info = {
                    "present": True,
                    "scheme": parsed.scheme,
                    "host": parsed.hostname,
                    "database": parsed.path.lstrip("/")
                }
            except Exception:
                db_info = {"present": True, "parse_error": True}
        else:
            db_info = {"present": False}'''

if '"DATABASE_URL": db_info' not in content:
    # Find the environment_variables section and update it
    import re
    env_pattern = r'("environment_variables":\s*\{[^}]+)'
    match = re.search(env_pattern, content)
    if match:
        old_env = match.group(1)
        new_env = old_env.rstrip() + ',\n                "DATABASE_URL": db_info'
        content = content.replace(old_env, new_env)
        
        # Insert db_info setup before return statement
        return_pattern = r'(\s+return\s+\{\s+"timestamp")'
        content = re.sub(return_pattern, '\n' + debug_update + r'\n\1', content)

# Add dbcheck endpoint
dbcheck_endpoint = '''

@app.get("/dbcheck")
async def db_check():
    """Attempt a lightweight DB connection to confirm Postgres wiring."""
    try:
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            return {"ok": False, "reason": "DATABASE_URL not set"}
        # Lazy import psycopg2 only when needed
        import psycopg2
        from psycopg2.extras import RealDictCursor
        conn = psycopg2.connect(db_url)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT version();")
        version = cur.fetchone()
        cur.close()
        conn.close()
        parsed = urlparse(db_url)
        return {
            "ok": True,
            "host": parsed.hostname,
            "database": parsed.path.lstrip("/"),
            "server_version": version[0] if isinstance(version, (list, tuple)) else version.get('version') if version else 'Unknown',
        }
    except Exception as e:
        logger.error(f"[DBCheck] Error: {e}")
        return {"ok": False, "error": str(e)}'''

if '@app.get("/dbcheck")' not in content:
    # Add after the debug endpoint
    content = content.replace(
        '        return {"error": str(e)}',
        '        return {"error": str(e)}' + dbcheck_endpoint
    )

# Write the updated file
with open('webhook_main.py', 'w') as f:
    f.write(content)

print("✅ Updated webhook_main.py with DB visibility features")
