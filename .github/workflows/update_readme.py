import re
import requests
from datetime import datetime

# ── Config ────────────────────────────────────────────────
GITHUB_USERNAME   = "esha-dey-22"
LEETCODE_USERNAME = "ed0629"
README_PATH       = "README.md"
CERTS_COUNT       = 3

GRAPHQL_URL = "https://leetcode.com/graphql"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent":   "Mozilla/5.0",
    "Referer":      "https://leetcode.com"
}

# ── Fetchers ──────────────────────────────────────────────

def fetch_leetcode_stats():
    query = """
    query getUserProfile($username: String!) {
        matchedUser(username: $username) {
            submitStats {
                acSubmissionNum {
                    difficulty
                    count
                }
            }
            tagProblemCounts {
                advanced     { tagName problemsSolved }
                intermediate { tagName problemsSolved }
                fundamental  { tagName problemsSolved }
            }
        }
    }
    """
    try:
        res = requests.post(
            GRAPHQL_URL,
            json={"query": query, "variables": {"username": LEETCODE_USERNAME}},
            headers=HEADERS,
            timeout=10
        )
        data = res.json()["data"]["matchedUser"]
        stats = {
            s["difficulty"]: s["count"]
            for s in data["submitStats"]["acSubmissionNum"]
        }

        all_tags = (
            data["tagProblemCounts"]["fundamental"] +
            data["tagProblemCounts"]["intermediate"] +
            data["tagProblemCounts"]["advanced"]
        )
        top_tags = sorted(
            all_tags,
            key=lambda x: x["problemsSolved"],
            reverse=True
        )[:5]
        tag_names = ", ".join(t["tagName"] for t in top_tags)

        return {
            "total":    stats.get("All",    0),
            "easy":     stats.get("Easy",   0),
            "medium":   stats.get("Medium", 0),
            "hard":     stats.get("Hard",   0),
            "top_tags": tag_names
        }
    except Exception as e:
        print(f"⚠️  LeetCode fetch failed: {e}")
        return None


def fetch_github_stats():
    try:
        res = requests.get(
            f"https://api.github.com/users/{GITHUB_USERNAME}",
            headers={"Accept": "application/vnd.github+json"},
            timeout=10
        )
        data = res.json()
        return {
            "repos":     data.get("public_repos", 0),
            "followers": data.get("followers",    0),
            "following": data.get("following",    0)
        }
    except Exception as e:
        print(f"⚠️  GitHub fetch failed: {e}")
        return None

# ── Updaters ──────────────────────────────────────────────

def replace_between(content, start_marker, end_marker, new_content):
    pattern = rf"{re.escape(start_marker)}.*?{re.escape(end_marker)}"
    replacement = f"{start_marker}{new_content}{end_marker}"
    result, count = re.subn(pattern, replacement, content, flags=re.DOTALL)
    if count == 0:
        print(f"⚠️  Marker not found: {start_marker}")
    return result


def update_readme(lc, gh):
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    if lc:
        total    = lc["total"]
        top_tags = lc["top_tags"]

        # 1. Update LEETCODE_TOTAL marker — only exists in the bullet point now
        content = re.sub(
            r"<!-- LEETCODE_TOTAL -->\d+<!-- /LEETCODE_TOTAL -->",
            f"<!-- LEETCODE_TOTAL -->{total}<!-- /LEETCODE_TOTAL -->",
            content
        )

        # 2. Update Stats At a Glance table
        repos_display = f"{gh['repos']}+" if gh else "24+"
        new_table = f"""
| 🔥 Streak | 📦 Repos | 🧠 LeetCode | 🎓 Certs |
|---|---|---|---|
| Active Daily | {repos_display} Public | {total}+ Solved | {CERTS_COUNT} Earned |
"""
        content = replace_between(
            content,
            "<!-- STATS_TABLE_START -->",
            "<!-- STATS_TABLE_END -->",
            new_table
        )

        # 3. Update LeetCode summary blockquote
        new_summary = f"""
> **{total}+ problems solved** — {top_tags} · Languages: Java, Python, JavaScript
"""
        content = replace_between(
            content,
            "<!-- LEETCODE_SUMMARY_START -->",
            "<!-- LEETCODE_SUMMARY_END -->",
            new_summary
        )

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ README updated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    if lc:
        print(f"   LeetCode : {lc['total']} solved "
              f"({lc['easy']}E / {lc['medium']}M / {lc['hard']}H)")
    if gh:
        print(f"   GitHub   : {gh['repos']} repos, "
              f"{gh['followers']} followers")


# ── Main ──────────────────────────────────────────────────

if __name__ == "__main__":
    print("Fetching LeetCode stats...")
    lc = fetch_leetcode_stats()

    print("Fetching GitHub stats...")
    gh = fetch_github_stats()

    update_readme(lc, gh)
