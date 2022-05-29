from annotation.models import Article, Annotated, Job, UserProfile
from django.db.models import Count
from django.utils import timezone

import numpy as np


# 每篇文章需要的标注者数量
MAX_ANNOTATED = 3
# 可以容忍的标注者最大延迟次数
MAX_NUM_DELAY = 3


def assign(uid: int, job_size: int, job_type: int, tested: bool = False) -> int:
    """
    :param uid: 用户 id
    :param job_size: 任务所需标注的文章数
    :param job_type: 任务类型
    :param tested: 是否在做测试
    :return: 任务分配状态
    """

    # 0 -> 用户无自由申请权限
    # 1 -> 用户任务过期次数过多，已被系统标注为不靠谱并自动淘汰
    # 2 -> 用户未完成上一轮任务
    # 3 -> 标注已完成，无法分配新任务
    # 4 -> 任务分配成功

    # 如果任务类型是自由申请，但用户无自由申请权限
    if job_type == 1 and UserProfile.objects.get(uid=uid).role != 2:
        if not tested:
            return 0

    # 查询用户过期的任务数量
    # if Job.objects.filter(uid=uid, is_expired=True).count() >= MAX_NUM_DELAY:
    #     return 1

    # 查询用户当前的任务列表
    current_jobs = Job.objects.filter(uid=uid, job_type=job_type)

    # 如果任务列表不为空，且最近任务未完成，则无法获取新任务
    if current_jobs and current_jobs.last().status == 0:
        if not tested:
            return 2

    # 查询有效的任务列表
    valid_jobs = Job.objects.filter(is_expired=False)

    # 查询有效的标注记录，以字典形式给出 key (文章id) -> value (被标注次数)
    all_annotated_ids = {
        instance.get('id'): instance.get('counts') for instance in Annotated.objects.filter(
            job_id__in=[job.job_id for job in valid_jobs]
        ).values('id').annotate(counts=Count('id')).order_by()
    }

    # 标注者自身已经标注的文章，以字典形式给出 key (文章id) -> 1
    self_annotated_ids = {
        instance.id: 1 for instance in Annotated.objects.filter(
            job_id__in=[job.job_id for job in valid_jobs.filter(uid=uid)])
    }

    # 被挑选的文章列表 与 其对应被选择的概率列表
    candidate_articles = Article.objects.all()
    prob = np.zeros(shape=(candidate_articles.count(),))

    # 文章被选中的概率计算方法：
    # 1）如果该文章已被该用户标注 或 标注次数等于最大标注次数，则其被选中的概率为 0
    # 2）否则该文章被选中的概率为 (已被标注次数 + 1) ^ 4 / log(摘要中句子的个数 + 1)
    for index, article in enumerate(candidate_articles):
        ratio = np.log(article.num_segments + 1)
        if article.id in all_annotated_ids:
            if article.id not in self_annotated_ids:
                annotated_counts = all_annotated_ids.get(article.id)
                if annotated_counts < MAX_ANNOTATED:
                    prob[index] = (annotated_counts + 1) ** 2 / (ratio * len(all_annotated_ids))
        else:
            prob[index] = 1 / (ratio * len(candidate_articles))

    # 可选择的文章数量为 0，说明无法分配更多的文章
    num_assignable = sum(prob != 0)
    if num_assignable == 0:
        return 3

    # 开始抽样
    assigned_articles = np.random.choice(
        candidate_articles, size=min(job_size, num_assignable), p=prob / np.sum(prob), replace=False)

    created = timezone.now()  # 创建时间
    expired = created + timezone.timedelta(weeks=1)  # 失效时间

    # 新建任务
    job = Job(
        uid=uid, job_progress=0, job_size=len(assigned_articles),
        reward=np.sum(np.array([article.get_price() for article in assigned_articles])),
        status=0, job_type=job_type, created=created, expired=expired, is_expired=False,
    )
    job.save()

    # 初始化标注结果表
    assigned = []
    for article in assigned_articles:
        assigned.append(Annotated(job_id=job.job_id, id=article.id))
    Annotated.objects.bulk_create(assigned)

    return 4
