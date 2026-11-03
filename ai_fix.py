# using print() for messages; no need for curses.echo
import os
import re
import sys
from pathlib import Path

APP_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("app")
TARGET = APP_DIR / "UserController.java"

VULN_SNIPPET = """import java.sql.*;

public class UserController {
    public ResultSet getUser(Connection connection, String userId) throws Exception {
        String query = "SELECT * FROM users WHERE id = " + userId;
        Statement stmt = connection.createStatement();
        return stmt.executeQuery(query);
    }
}
"""

FIXED_SNIPPET = """import java.sql.*;

public class UserController {
    public ResultSet getUser(Connection connection, String userId) throws Exception {
        String query = "SELECT * FROM users WHERE id = ?";
        PreparedStatement stmt = connection.prepareStatement(query);
        stmt.setString(1, userId);
        return stmt.executeQuery();
    }
}
"""

def try_openai_fix(code: str) -> str | None:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("OpenAI API key not set, skipping AI-generated fix")
        return None

    print("OpenAI API key found, attempting AI-generated fix")

    try:
        from openai import OpenAI
    except ModuleNotFoundError:
        print("OpenAI SDK not installed, skipping AI-generated fix")
        return None

    try:
        client = OpenAI(api_key=api_key)
        prompt = f"""
You are a senior Java security engineer.

Fix the SQL injection vulnerability in this Java code.
Requirements:
- Use PreparedStatement
- Keep the class name and method signature
- Return ONLY valid Java code

Code:
{code}
"""
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        content = response.choices[0].message.content or ""
        content = content.strip()

        # strip fenced code if present
        if content.startswith("```"):
            content = re.sub(r"^```[a-zA-Z0-9]*\n?", "", content)
            content = re.sub(r"\n```$", "", content)

        if "PreparedStatement" in content and "executeQuery()" in content:
            return content
        print("OpenAI response did not match expected fix shape, using fallback")
        return None
    except Exception as e:
        print(f"OpenAI fix unavailable: {e}")
        return None

def fallback_fix(code: str) -> str:
    
    print("Applying deterministic fallback fix for SQL injection vulnerability")
    
    if 'String query = "SELECT * FROM users WHERE id = " + userId;' in code and \
       'Statement stmt = connection.createStatement();' in code and \
       'return stmt.executeQuery(query);' in code:
        return FIXED_SNIPPET

    # generic fallback for demo
    patched = code
    patched = patched.replace(
        'String query = "SELECT * FROM users WHERE id = " + userId;',
        'String query = "SELECT * FROM users WHERE id = ?";'
    )
    patched = patched.replace(
        'Statement stmt = connection.createStatement();',
        'PreparedStatement stmt = connection.prepareStatement(query);'
    )
    patched = patched.replace(
        'return stmt.executeQuery(query);',
        'stmt.setString(1, userId);\n        return stmt.executeQuery();'
    )
    if "PreparedStatement" in patched:
        if "import java.sql.*;" not in patched and "PreparedStatement" not in code:
            patched = "import java.sql.PreparedStatement;\n" + patched
        return patched
    return FIXED_SNIPPET

def main():
    if not TARGET.exists():
        print(f"ERROR: File not found: {TARGET}")
        sys.exit(1)

    code = TARGET.read_text(encoding="utf-8")

    print("===> AI analyzing findings")
    fixed = try_openai_fix(code)

    if fixed:
        print("===> Applied OpenAI-generated fix")
    else:
        print("===> OpenAI unavailable, using deterministic demo fix")
        fixed = fallback_fix(code)

    TARGET.write_text(fixed, encoding="utf-8")
    print(f"===> Updated file: {TARGET}")

if __name__ == "__main__":
    main()
