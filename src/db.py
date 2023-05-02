import sqlite3, os, threading
from util import init_data_dir


def get_db():
    conn = sqlite3.connect(os.path.join(init_data_dir(), 'article.db'))
    cursor = conn.cursor()
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS "article" (
            "id" INTEGER NOT NULL,
            "title" TEXT NOT NULL,
            "time" TEXT NOT NULL,
            "content" TEXT NOT NULL,
            "main_type" TEXT NOT NULL,
            "sub_type" TEXT,
            PRIMARY KEY("id" AUTOINCREMENT)
        )
    '''
    )
    return conn, cursor


def insert_article(article_data, conn, cursor):
    try:
        cursor.execute(
            'insert into "article" ("title", "time", "content", "main_type", "sub_type") VALUES (?, ?, ?, ?, ?)',
            article_data,
        )
    except Exception as e:
        article_data[2] = ''
        print(f'插入失败，{e}', article_data)
    conn.commit()


def insert_article_db(all_article: list):
    threads = []
    conn, cursor = get_db()
    finish_count = 0
    all_count = len(all_article)
    for article in all_article:
        finish_count += 1
        print(f'\r数据库插入进度：{finish_count}/{all_count}', end='')
        if not article:
            continue
        insert_article(article, conn, cursor)
    cursor.close()
    conn.close()
