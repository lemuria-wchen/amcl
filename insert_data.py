import json
import time
from tqdm import tqdm
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'amcl.settings')
django.setup()

from annotation.models import Article
from annotation.utils.translate import BDT


# 插入数据
with open('samples.json', 'r', encoding='utf-8') as f:
    target_articles = json.load(f)

db_articles = []
for article in target_articles:
    db_articles.append(Article(**article, version=1))

Article.objects.bulk_create(db_articles)


# 利用百度翻译，翻译英文摘要
translator = BDT()

for article in tqdm(Article.objects.all()):

    if article.transl_sentences is None:
        try:
            article.transl_sentences = json.dumps(
                translator.translate('\n'.join(json.loads(article.sentences))), ensure_ascii=False)
            article.save()
            # 百度翻译API有请求频率限制
            time.sleep(1)
        except Exception as e:
            print(e)
            translator = BDT()

    if article.transl_abstract is None:
        try:
            article.transl_abstract = translator.translate(article.abstract)[0]
            article.save()
            time.sleep(1)
        except Exception as e:
            print(e)
            translator = BDT()
