"""3-D: 蓄積ライブラリの壁打ち検索"""

import os
import sys
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from src.shared.db.client import DirectionDB
from src.shared.embedding import get_embedding

logger = logging.getLogger("module3")


def search_by_text_query(query, limit=10):
    """自然言語クエリでセマンティック検索（ベクトル類似度）"""
    query_embedding = get_embedding(query)
    db = DirectionDB()
    db.connect()
    results = db.search_by_text(query_embedding, limit=limit, source_type="reference")
    db.close()

    formatted = []
    for r in results:
        formatted.append({
            "file_name": r["file_name"],
            "file_path": r["file_path"],
            "text": r["text"][:200],
            "similarity": round(float(r["similarity"]), 3),
            "start_tc": r["start_tc"],
            "end_tc": r["end_tc"],
        })
    logger.info(f"セマンティック検索: '{query}' → {len(formatted)}件")
    return formatted


def search_by_keyword(keyword, limit=10):
    """キーワードで文字起こしテキストを検索"""
    db = DirectionDB()
    db.connect()
    results = db.search_by_keyword(keyword, limit=limit)
    db.close()

    formatted = []
    for r in results:
        formatted.append({
            "file_name": r["file_name"],
            "file_path": r["file_path"],
            "text": r["text"][:200],
            "start_tc": r["start_tc"],
            "end_tc": r["end_tc"],
        })
    logger.info(f"キーワード検索: '{keyword}' → {len(formatted)}件")
    return formatted


def search_by_tags(tags, limit=10):
    """タグの組み合わせで検索

    Args:
        tags: dict (例: {"composition": "オープニング", "mood": "派手"})
    """
    db = DirectionDB()
    db.connect()

    conditions = []
    params = []
    for category, tag_name in tags.items():
        conditions.append("EXISTS (SELECT 1 FROM scene_tags st WHERE st.scene_id = s.id AND st.category = %s AND st.tag_name = %s)")
        params.extend([category, tag_name])

    where_clause = " AND ".join(conditions) if conditions else "TRUE"

    with db.conn.cursor(cursor_factory=__import__('psycopg2.extras', fromlist=['RealDictCursor']).RealDictCursor) as cur:
        cur.execute(f"""
            SELECT s.*, ma.file_name, ma.file_path,
                   (SELECT array_agg(st.category || ':' || st.tag_name)
                    FROM scene_tags st WHERE st.scene_id = s.id) as tags
            FROM scenes s
            JOIN media_assets ma ON s.asset_id = ma.id
            WHERE {where_clause}
            ORDER BY s.created_at DESC
            LIMIT %s
        """, params + [limit])
        results = cur.fetchall()

    db.close()

    formatted = []
    for r in results:
        formatted.append({
            "file_name": r["file_name"],
            "file_path": r["file_path"],
            "scene_index": r["scene_index"],
            "start_tc": r["start_tc"],
            "end_tc": r["end_tc"],
            "classification": r["classification"],
            "grid_image": r["grid_image_path"],
            "tags": r.get("tags", []),
        })
    logger.info(f"タグ検索: {tags} → {len(formatted)}件")
    return formatted


def search_combined(query=None, keyword=None, tags=None, limit=10):
    """複合検索: セマンティック + キーワード + タグを組み合わせ"""
    results = {}

    if query:
        results["semantic"] = search_by_text_query(query, limit)

    if keyword:
        results["keyword"] = search_by_keyword(keyword, limit)

    if tags:
        results["tags"] = search_by_tags(tags, limit)

    return results
