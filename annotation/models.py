from django.db import models

import string
import json
import numpy as np


# 定义待标注样例
class TagManager(models.Manager):
    def get_queryset(self):
        samples = super().get_queryset().exclude(
            abstract__contains='All rights reserved').exclude(
            abstract__contains='(C)').exclude(
            num_segments__gt=18).exclude(
            num_segments__lt=3).filter(
            abstract__endswith='.'
        )
        np.random.seed(0)
        ids = np.random.choice([sample.id for sample in samples], 2000, replace=False)
        return samples.filter(id__in=ids)


# 定义测试样例
class EntranceManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(doi__in=[
            '10.1007/s00382-010-0977-x',
            '10.1016/j.envint.2009.07.001',
        ])


# 文章信息表
class Article(models.Model):
    # 文章 id，文章信息表的主键
    id = models.AutoField(primary_key=True, help_text='article id')

    # 文章 doi（添加了索引） 与 文章标题
    doi = models.CharField(max_length=250, help_text='digital object unique identifier <DOI> of article', db_index=True)
    title = models.CharField(max_length=1000, null=True, blank=True, help_text='article title')

    # 作者名列表 与 通讯作者信息
    au = models.TextField(null=True, blank=True, help_text='abbreviated names list of authors')
    rp = models.TextField(null=True, blank=True, help_text='reprint author')

    # 文章发表所在期刊 与 文章发布年份
    journal = models.CharField(max_length=250, null=True, blank=True, help_text='publication journal')
    year = models.IntegerField(null=True, blank=True, help_text='publication year')

    # 文章摘要 与 摘要句子列表（使用分句算法进行分句）
    abstract = models.TextField(null=True, blank=True, help_text='abstract')
    sentences = models.TextField(null=True, blank=True, help_text='segmented sentences of abstract')

    # 摘要句子个数
    num_segments = models.IntegerField(null=True, blank=True, help_text='number of segments')

    # 文章摘要中文翻译 与 摘要句子列表中文翻译
    transl_abstract = models.TextField(null=True, blank=True, help_text='translated abstract')
    transl_sentences = models.TextField(null=True, blank=True, help_text='translated segmented sentences of abstract')

    # 文章关键词
    keyword = models.CharField(max_length=1000, null=True, blank=True, help_text='keywords')

    # 研究类别
    wc = models.CharField(max_length=250, null=True, blank=True, help_text='research areas')
    sc = models.CharField(max_length=250, null=True, blank=True, help_text='web of science categories')

    # 标准国际刊号
    sn = models.CharField(max_length=100, null=True, blank=True,
                          help_text='unique identifier assigned to a newspaper, journal, yearbook, etc. '
                                    '< international standard serial number >')
    # 引用数 和 被引用数
    cited = models.IntegerField(null=True, blank=True, default=0, help_text='cited references counts')
    citing = models.IntegerField(null=True, blank=True, default=0,
                                 help_text='times cited counts in web of science database')

    topic_id = models.IntegerField(default=-1, null=True, blank=True, help_text='topic id of article')
    version = models.IntegerField(default=1, null=True, blank=True, help_text='version of article')

    # 展示的作者名字个数
    MAX_SHOWED_AUTHORS = 5
    # 每条句子的标注价格
    PRICE_PER_SEGMENT = 0.15
    # 每条句子的审核价格
    REVIEW_PRICE_PER_SEGMENT = 0.15 * 5
    # 每条句子预计的标注时间
    MINUTE_PER_SEGMENT = 0.6
    # 每条句子预计的审核时间
    REVIEW_MINUTE_PER_SEGMENT = 1

    # 所有的文章对象
    objects = models.Manager()

    # 所有待标注的文章对象
    tagged_objects = TagManager()
    # 入门测试的文章对象
    entrance_objects = EntranceManager()

    class Meta:
        db_table = 'article'
        ordering = ['id', ]

    def author_template(self):
        au_list = json.loads(self.au)
        if len(au_list) > self.MAX_SHOWED_AUTHORS:
            return '; '.join(au_list[: self.MAX_SHOWED_AUTHORS]) + '; et al.'
        else:
            return '; '.join(au_list)

    def title_template(self):
        return string.capwords(self.title)

    def journal_template(self):
        return string.capwords(self.journal) + ' ( ' + str(self.year) + ' )'

    def keyword_template(self):
        if self.keyword:
            return string.capwords("; ".join(json.loads(self.keyword)))
        else:
            return ''

    def sentences_template(self):
        return zip(json.loads(self.sentences), json.loads(self.transl_sentences))

    def get_sentences(self):
        return json.loads(self.sentences)

    def get_price(self):
        return self.PRICE_PER_SEGMENT * self.num_segments

    def get_review_price(self):
        return self.REVIEW_PRICE_PER_SEGMENT * self.num_segments

    def get_time(self):
        return self.MINUTE_PER_SEGMENT * self.num_segments

    def get_review_time(self):
        return self.REVIEW_MINUTE_PER_SEGMENT * self.num_segments


# 文章引用表
class Citation(models.Model):
    # 引用 id，引用表的主键
    id = models.AutoField(primary_key=True, help_text='citation id')
    # 原文章 doi 和该文章引用的文章 doi
    cite = models.CharField(max_length=250, help_text='article <DOI>', db_index=True)
    cited = models.CharField(max_length=250, help_text='cited article <DOI>', db_index=True)

    class Meta:
        db_table = 'citation'
        ordering = ['id', ]


# 用户信息表
class UserProfile(models.Model):
    gender_choices = (
        (0, 'male'), (1, 'female')
    )
    education_choices = (
        (0, 'BS/BA'), (1, 'MS'), (2, 'PhD'),
    )
    role_choices = (
        (0, 'unactivated'), (1, 'activated'), (2, 'accessed'), (3, 'reviewer'),
    )
    school_choices = (
        (0, '中国语言文学系'), (1, '外国语言文学学院'), (2, '历史学系'), (3, '旅游学系'),
        (4, '文物与博物馆学系'), (5, '哲学学院'), (6, '法学院'), (7, '国际关系与公共事务学院'),
        (8, '社会发展与公共政策学院'), (9, '新闻学院'), (10, '经济学院'), (11, '泛海国际金融学院'),
        (12, '马克思主义学院'), (13, '国际文化交流学院'), (14, '数学科学学院'), (15, '物理学系'),
        (16, '现代物理研究所/核科学与技术系'), (17, '化学系'), (18, '高分子科学系'), (19, '环境科学与工程系'),
        (20, '大气和海洋科学系'), (21, '信息科学与工程学院'), (22, '计算机科学技术学院'), (23, '软件学院'),
        (24, '微电子学院'), (25, '航天航空系'), (26, '材料科学系'), (27, '生命科学学院'),
        (28, '大数据学院'), (29, '管理学院'), (30, '基础医学院'), (31, '临床医学院'),
        (32, '公共卫生学院'), (33, '药学院'), (34, '护理学院'), (35, '继续教育学院'),
        (36, '体育教学部'), (37, '艺术教育中心'), (38, '分析测试中心'), (39, '实验动物科学部'),
        (40, '出土文献与古文字研究中心'), (41, '高等教育研究所'), (42, '古籍整理研究所'), (43, '国际问题研究院'),
        (44, '科技考古研究院'), (45, '六次产业研究院'), (46, '马克思主义研究院'), (47, '全球公共政策研究院'),
        (48, '社会科学高等研究院'), (49, '文史研究院'), (50, '一带一路及全球治理研究院'), (51, '中国历史地理研究所'),
        (52, '中国研究院'), (53, '大气科学研究院'), (54, '大数据试验场研究院'), (55, '大数据研究院'),
        (56, '代谢与整合生物学研究院'), (57, '复杂体系多尺度研究院'), (58, '工程与应用技术研究院'), (59, '类脑芯片与片上智能系统研究院'),
        (60, '类脑智能科学与技术研究院'), (61, '人类表型组研究院'), (62, '上海数学中心'), (63, '手性分子工程中心'),
        (64, '微纳电子器件与量子计算机研究院'), (65, '先进材料实验室'), (66, '智能复杂体系基础理论与关键技术'), (67, '智能机器人研究院'),
        (68, '放射医学研究所'), (69, '脑科学研究院'), (70, '生物医学研究院'), (71, '其他'),
    )
    # 用户 id，用户信息表主键
    uid = models.AutoField(primary_key=True, help_text='user id')
    # 用户电子邮件（用于账号的注册与激活）
    email = models.CharField(max_length=50, help_text='user email')
    # 学号（用于标注费用的结算）
    student_id = models.CharField(max_length=20, help_text='student id')
    # 用户名（由字母、数字、下划线组成，用户信息展示）
    username = models.CharField(max_length=30, help_text='username')
    # 用户真实名字（中文字符串）
    name = models.CharField(max_length=10, help_text='real name')
    # 用户手机号码
    phone_number = models.CharField(max_length=11, help_text='phone number')
    # 用户性别、教育程度、学院（用于标注用户身份信息统计）
    gender = models.IntegerField(choices=gender_choices, help_text='user gender')
    education = models.IntegerField(choices=education_choices, help_text='user education')
    school = models.IntegerField(choices=school_choices, help_text='school')
    # 用户密码
    password = models.CharField(max_length=500, help_text='password of registered user')
    # 用户状态（0 -> 注册未激活，1 -> 注册已激活，2 -> 拥有申请新任务权限，3 -> 管理员审核）
    role = models.IntegerField(default=0, choices=role_choices, help_text='role')
    # 用户注册时间 和 用户信息更新时间
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profile'
        ordering = ['uid', ]


# 邮件发送记录表
class EmailVerifyRecord(models.Model):
    # 用户在以下两种情况将会收到系统发送的邮件：（1）用户账号激活；（2）用户密码修改
    send_choices = (
        ('register', 'register'), ('reset', 'reset')
    )
    # 用户 id，用户信息表主键
    uid = models.IntegerField(help_text='user id')
    # 验证码，用于邮件中的 账号激活 或 重置密码 链接后缀
    captcha = models.CharField(max_length=100, help_text='verification code')
    # 验证码是否失效（如重置密码成功后，密码重置链接应该失效，避免用户可以重复使用链接修改密码）
    is_valid = models.BooleanField(default=True, help_text='whether the link with captcha is valid')
    # 邮件类型（注册或重置密码）
    send_type = models.CharField(choices=send_choices, max_length=10, help_text='activate or forget password')
    # 邮件发送时间
    send_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'email_verify_record'
        ordering = ['send_time', ]


# 任务表
class Job(models.Model):
    status_choices = (
        (0, '进行中'),  # 表示该任务正在进行中
        (1, '已完成'),  # 表示该任务已经完成
        (2, '已过期'),  # 表示该任务已过期
        (3, '已支付'),  # 表示该任务已完成了薪酬结算
    )
    job_type_choices = (
        (0, '系统分配'),  # 系统分配的任务，由管理员申请
        (1, '自由申请'),  # 用户自由申请的任务，由用户独立申请
    )
    # 任务 id，任务表的主键
    job_id = models.AutoField(primary_key=True, help_text='job id')
    # 用户 id，用户信息表主键（表示该任务和用户的一一对应关系）
    uid = models.IntegerField(help_text='user id')
    # 标注完成的文章数
    job_progress = models.IntegerField(default=0, help_text='number of articles have been annotated')
    # 需要标注的文章总数
    job_size = models.IntegerField(help_text='total number of articles to be annotated')
    # 当前的总薪酬
    reward_progress = models.FloatField(default=0.0, help_text='current reward')
    # 标注的总薪酬
    reward = models.FloatField(default=0.0, help_text='total reward')
    # 任务状态（进行中、已完成 或 已支付）
    status = models.IntegerField(choices=status_choices, help_text='job status')
    # 任务类型（系统分配 或 自由申请）
    job_type = models.IntegerField(choices=job_type_choices, help_text='job type')
    # 任务创建时间（系统分配 或 自由申请 任务成功时刻的时间戳）
    created = models.DateTimeField(help_text='job created time')
    # 任务完成时间（任务完成时系统自动更新）
    finished = models.DateTimeField(null=True, blank=True, help_text='job finished time')
    # 任务过期时间（默认为任务创建后的一周后，主要是给用户看的，实际上到底过不过期最终由管理员控制）
    expired = models.DateTimeField(help_text='job expired time')
    # 任务是否过期（如果用户未按时完成 job，管理员可以将这些任务设置为过期，此时这些任务对应的文章将能被继续分配）
    is_expired = models.BooleanField(default=False, help_text='whether the job is expired')

    class Meta:
        db_table = 'job'
        ordering = ['job_id', ]


# 标注结果表
class Annotated(models.Model):
    # 标注 id，标注表的主键
    aid = models.AutoField(primary_key=True, help_text='annotated id')
    # 任务 id，任务表的主键（用户文章列表可以按照文章 id 进行排序）
    job_id = models.IntegerField(help_text='job id')
    # 文章 id，文章表的主键
    id = models.IntegerField(help_text='article id')
    # 标注结果，可以被解析成 json 格式的字符串
    annotated = models.TextField(null=True, blank=True, help_text='annotated result')
    # 文章是否已被标注
    is_annotated = models.BooleanField(default=False, help_text='whether the article is annotated')
    # 上次访问该文章的时刻，方便记录每道题的标注用时 以及 再次访问的入口
    visited = models.DateTimeField(auto_now=True)
    # 该用户标注完当前文章所花的总时间（秒为单位）
    duration = models.IntegerField(default=0, help_text='job duration (seconds)')

    # version = models.IntegerField(default=0, null=True, blank=True, help_text='version of annotated')

    class Meta:
        db_table = 'annotated'
        ordering = ['job_id', 'id', ]

    def fetch_annotated(self):
        annotated = json.loads(self.annotated)
        return json.dumps(annotated.get('arg_type')), json.dumps(annotated.get('arg_rel')), annotated.get('diff')

    def arg_type_template(self):
        annotated = json.loads(self.annotated)
        return annotated.get('arg_type')

    def arg_rel_template(self):
        annotated = json.loads(self.annotated)
        return annotated.get('arg_rel')

    def diff_template(self):
        annotated = json.loads(self.annotated)
        return annotated.get('diff')

    def duration_template(self):
        return self.duration / 60


class Reviewed(models.Model):
    # 审核 id，审核表的主键
    rid = models.AutoField(primary_key=True, help_text='annotated id')
    # 文章 id，文章表的主键
    id = models.IntegerField(help_text='article id')
    # 用户 id，用户表的主键
    uid = models.IntegerField(default=1, help_text='user id')
    # 标注结果，可以被解析成 json 格式的字符串
    reviewed = models.TextField(null=True, blank=True, help_text='reviewed result')

    class Meta:
        db_table = 'reviewed'
        ordering = ['id', ]

    def fetch_annotated(self):
        annotated = json.loads(self.reviewed)
        return json.dumps(annotated.get('arg_type')), json.dumps(annotated.get('arg_rel'))

    def annotated_template(self):
        annotated = json.loads(self.reviewed)
        return annotated
