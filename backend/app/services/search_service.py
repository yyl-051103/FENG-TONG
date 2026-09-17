"""
ES 搜索服务 — 索引管理 / 全文搜索 / 新闻同步 / 删除
"""
import logging
import re
import html
import jieba
from elasticsearch import AsyncElasticsearch
from app.config import ES_HOST

logger = logging.getLogger(__name__)

es_client = AsyncElasticsearch(ES_HOST)

NEWS_INDEX = "news_index"


def tokenize_text(text: str) -> str:
    """使用jieba搜索引擎模式分词，返回空格连接的词组。分词前清洗HTML标签和实体字符。"""
    if not text:
        return ""
    # 1. 移除 HTML 标签
    text = re.sub(r'<[^>]+>', ' ', text)
    # 2. 解码 HTML 实体（&ldquo; → " 等）
    text = html.unescape(text)
    # 3. 合并多余空白
    text = re.sub(r'\s+', ' ', text).strip()
    jieba.setLogLevel(jieba.logging.INFO)
    return " ".join(jieba.cut_for_search(text))


async def init_index():
    """创建ES索引（如果不存在）"""
    exists = await es_client.indices.exists(index=NEWS_INDEX)
    if not exists:
        await es_client.indices.create(index=NEWS_INDEX, body={
            "mappings": {
                "properties": {
                    "id": {"type": "integer"},
                    "title": {"type": "text", "analyzer": "standard"},
                    "content": {"type": "text", "analyzer": "standard"},
                    "title_tokens": {"type": "text", "analyzer": "whitespace"},
                    "content_tokens": {"type": "text", "analyzer": "whitespace"},
                    "source": {"type": "keyword"},
                    "status": {"type": "keyword"},
                    "risk_level": {"type": "keyword"},
                    "province": {"type": "keyword"},
                    "city": {"type": "keyword"},
                    "user_id": {"type": "integer"},
                    "nickname": {"type": "keyword"},
                    "create_time": {"type": "date"}
                }
            }
        })


async def search_news(query: str, page: int = 1, size: int = 10):
    """ES全文搜索 — jieba分词 + 原始字段双路召回，返回高亮结果+分页"""
    from_ = (page - 1) * size
    query_tokens = tokenize_text(query)
    try:
        result = await es_client.search(index=NEWS_INDEX, body={
            "query": {
                "bool": {
                    "should": [
                        {"match": {"title_tokens": query_tokens}},
                        {"match": {"content_tokens": query_tokens}}
                    ],
                    "minimum_should_match": 1,
                    "filter": [
                        {"term": {"status": "已通过"}}
                    ]
                }
            },
            "highlight": {
                "fields": {
                    "title_tokens": {"number_of_fragments": 0},
                    "content_tokens": {"fragment_size": 150, "number_of_fragments": 1}
                }
            },
            "from": from_,
            "size": size,
            "sort": [{"create_time": {"order": "desc"}}]
        }, request_timeout=3)

        total = result["hits"]["total"]["value"]
        hits = []
        for hit in result["hits"]["hits"]:
            source = hit["_source"]
            source["highlight_title"] = hit.get("highlight", {}).get("title_tokens", [source.get("title", "")])[0]
            source["highlight_content"] = hit.get("highlight", {}).get("content_tokens", [""])[0]
            hits.append(source)

        return {"total": total, "items": hits}
    except Exception as e:
        logger.error(f"ES搜索失败: {e}")
        return {"total": 0, "items": []}


async def sync_news(news_dict: dict):
    """将新闻写入ES索引"""
    try:
        await es_client.index(index=NEWS_INDEX, id=news_dict["id"], document=news_dict)
    except Exception:
        pass  # 异步写入，失败不影响主流程


async def delete_news(news_id: int):
    """从ES删除新闻文档"""
    try:
        await es_client.delete(index=NEWS_INDEX, id=str(news_id))
    except Exception:
        pass


async def sync_all_news():
    """将MySQL中所有已通过的新闻全量同步到ES"""
    from app.database import SessionLocal
    from app.models.news import News
    from app.models.user import User

    db = SessionLocal()
    try:
        news_list = db.query(News).filter(News.status == "已通过").all()
        count = 0
        for news in news_list:
            user = db.query(User).filter(User.id == news.user_id).first()
            title = news.title or ""
            content = news.content or ""
            news_dict = {
                "id": news.id,
                "title": title,
                "content": content,
                "title_tokens": tokenize_text(title),
                "content_tokens": tokenize_text(content),
                "source": getattr(news, "source", None),
                "status": news.status,
                "risk_level": getattr(news, "risk_level", None),
                "province": getattr(news, "province", None),
                "city": getattr(news, "city", None),
                "user_id": news.user_id,
                "nickname": user.nickname if user else None,
                "create_time": news.create_time.isoformat() if news.create_time else None
            }
            await sync_news(news_dict)
            count += 1
        print(f"全量同步完成: {count} 条新闻已写入ES")
        return count
    finally:
        db.close()


async def close_es():
    await es_client.close()
