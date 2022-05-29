from django.shortcuts import render, redirect, Http404
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Sum, Count

from django.utils import timezone
from django.db.utils import DataError

from .models import Article, UserProfile, EmailVerifyRecord, Annotated, Job, Reviewed
from .forms import UserLoginForm, UserRegisterForm, PasswordForgetForm, PasswordResetForm

from .utils.mail import send_register_email
from .utils.job import assign, MAX_ANNOTATED
from .utils.agreement import agreement_arg_type, agreement_arg_relation, \
    agreement_arg_relation_double, agreement_arg_type_double


import re
import json
import datetime


EMAIL_PATTERN = re.compile(r'^([\w]+\.*)([\w]+)@[\w]+\.\w{3}(\.\w{2}|)$')
USERNAME_PATTERN = re.compile(r'^(?!_)(?!.*?_$)[a-zA-Z0-9_\u4e00-\u9fa5]+$')
PHONE_NUMBER_PATTERN = re.compile(r'^1(3\d|4[4-9]|5[0-35-9]|6[67]|7[013-8]|8[0-9]|9[0-9])\d{8}$')

ACCOUNT_VERIFY_EXPIRED = 7200  # 7,200 seconds, which is 2 hours
PRICE_PER_RECORD = 1  # price to annotate an article
NUM_RECORDS_PER_APPLY = 20  # num of records per round

JOB_SIZE_DICT = {
    '0': 10, '1': 15, '2': 20,
}

JOB_APPLY_MESSAGE = {
    0: '您暂时没有自由申请新任务的权限！',
    1: '您逾期未完成的任务次数过多，系统已取消您申请新任务的权限！',
    2: '您还有任务未完成，请先完成已申请的任务！',
    3: '标注流程已结束，已无法分配新任务！',
    4: '任务分配成功！',
}


def chunks(obj, chunk_size):
    chunk_size = max(1, chunk_size)
    return (obj[_: _ + chunk_size] for _ in range(0, len(obj), chunk_size))


# 定义装饰器
def require_login(fn):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('is_login', False):
            return redirect('login')
        else:
            return fn(request, *args, **kwargs)

    return wrapper


# 用户登录
def login(request):
    # 如果 request 是 post 请求，则对登录信息进行验证
    if request.method == 'POST':
        login_form = UserLoginForm(request.POST)
        message = 'Incorrect username or password.'
        if login_form.is_valid():
            username = login_form.cleaned_data['username']
            password = login_form.cleaned_data['password']
            try:
                if EMAIL_PATTERN.match(username):
                    user = UserProfile.objects.get(email=username)
                else:
                    user = UserProfile.objects.get(username=username)
                if user.role != 0:
                    if check_password(password, user.password):
                        # 保存 session 会话信息（存储用户的登录状态、用户id及用户名等信息）
                        request.session['is_login'] = True
                        request.session['uid'] = user.uid
                        request.session['username'] = user.username
                        # 如果登录验证通过，重定向到任务主页
                        return redirect('am')
                    else:
                        message = 'Incorrect password.'
                else:
                    message = 'Unverified account.'
            except UserProfile.DoesNotExist:
                message = 'Invalid email or username.'
        return render(request, 'account/login.html', {'message': message, 'login_form': login_form})
    # 否则给出原始登录界面
    login_form = UserLoginForm()
    return render(request, 'account/login.html', {'login_form': login_form})


# 用户注册
def register(request):
    # 如果 request 是 post 请求，则对注册信息进行验证
    if request.method == 'POST':
        register_form = UserRegisterForm(request.POST)
        is_registered, message, user = False, '', None
        if register_form.is_valid():
            # 这些验证字段的逻辑后期可以写在 form 里，现在就暂时这样吧，虽然代码看起来很丑陋
            email = register_form.cleaned_data['email']
            name = register_form.cleaned_data['name']
            student_id = register_form.cleaned_data['student_id']
            username = register_form.cleaned_data['username']
            phone_number = register_form.cleaned_data['phone_number']
            gender = register_form.cleaned_data['gender']
            education = register_form.cleaned_data['education']
            school = register_form.cleaned_data['school']
            password = register_form.cleaned_data['password']
            repeated_password = register_form.cleaned_data['repeated_password']
            # 这些验证字段的逻辑后期可以写在 form 里，现在就暂时这样吧，虽然代码看起来很丑陋
            if UserProfile.objects.filter(email=email):
                message = 'The email has been registered, please login directly.'
            else:
                if email.endswith('edu.cn'):
                    if UserProfile.objects.filter(username=username):
                        message = 'The username has been registered.'
                    else:
                        if USERNAME_PATTERN.fullmatch(username):
                            if PHONE_NUMBER_PATTERN.fullmatch(phone_number):
                                if password != repeated_password:
                                    message = 'Inconsistent password.'
                                else:
                                    try:
                                        # 将用户注册数据存储到数据库
                                        user = UserProfile(
                                            email=email, student_id=student_id, name=name, username=username,
                                            gender=gender, phone_number=phone_number, education=education,
                                            school=school, password=make_password(password))
                                        user.save()
                                        is_registered = True
                                    except DataError:
                                        message = 'Registration failed.'
                                    if is_registered:
                                        # 发送账号激活的电子邮件
                                        status = send_register_email(user=user, send_type='register')
                                        if not status:
                                            # 将用户注册的数据从数据库中删除
                                            UserProfile.objects.filter(email=email).all().delete()
                                            is_registered = False
                                            message = 'Failed to send account activation email.'
                            else:
                                message = 'Invalid phone number.'
                        else:
                            message = 'Invalid username.'
                else:
                    message = 'Either illegal email format or not an education email.'
        return render(request, 'account/register.html', {
            'message': message, 'register_form': register_form, 'is_registered': is_registered,
        })
    register_form = UserRegisterForm()
    return render(request, 'account/register.html', {'register_form': register_form})


# 账号激活
def activate(request, captcha):
    try:
        record = EmailVerifyRecord.objects.get(captcha=captcha)
    except EmailVerifyRecord.DoesNotExist:
        raise Http404

    message, username = '', ''

    # 如果邮件激活时间和注册时间相差超过2个小时，则要求用户重新注册
    if (timezone.now() - record.send_time).seconds > ACCOUNT_VERIFY_EXPIRED:
        message = 'Expired account verification link, please register again.'
        UserProfile.objects.filter(email=record.email).all().delete()
    elif not record.is_valid:
        message = 'Account already activated.'
    else:
        user = UserProfile.objects.get(uid=record.uid)
        user.role = 1
        username = user.username
        user.save()
        # 验证完后，链接就可以失效了
        record.is_valid = False
        record.save()

    return render(request, 'account/activate.html', {
        'message': message,
        'username': username,
    })


# 忘记密码
def forget(request):
    # 如果用户忘记了密码或想修改密码，则发送一封密码重置的邮件到用户的邮箱
    if request.method == 'POST':
        forget_form = PasswordForgetForm(request.POST)
        message, is_sent = '', False
        if forget_form.is_valid():
            # 从表单中获取用户邮件
            email = forget_form.cleaned_data['email']
            try:
                # 通过邮件找到用户信息
                user = UserProfile.objects.get(email=email)
                # 向用户邮箱发送邮件
                status = send_register_email(user=user, send_type='reset')
                if status:
                    is_sent = True
                else:
                    message = 'Sending email failed.'
            except UserProfile.DoesNotExist:
                message = 'Unregistered email address.'
        return render(request, 'account/forget.html', {
            'forget_form': forget_form, 'message': message, 'is_sent': is_sent})

    forget_form = PasswordForgetForm()
    return render(request, 'account/forget.html', {'forget_form': forget_form})


# 重置密码
def reset(request, captcha):
    reset_form = PasswordResetForm(request.POST)
    try:
        record = EmailVerifyRecord.objects.get(captcha=captcha)
    except EmailVerifyRecord.DoesNotExist:
        raise Http404

    # 如果密码修改时间和请求修改时间相差超过2个小时，则要求用户重新发送重置密码邮件
    if (timezone.now() - record.send_time).seconds > ACCOUNT_VERIFY_EXPIRED:
        record.is_valid = False

    # 验证码是否有效
    is_valid = record.is_valid

    if request.method == 'POST':
        message, updated = '', False
        if reset_form.is_valid():
            password = reset_form.cleaned_data['password']
            repeated_password = reset_form.cleaned_data['repeated_password']
            if password == repeated_password:
                try:
                    UserProfile.objects.filter(
                        uid=record.uid).update(password=make_password(password))
                    updated = True
                except DataError:
                    message = 'Password reset failed.'
                # 如果成功更改，更新数据库中的记录
                if updated:
                    record.is_valid = False
                    record.save()
            else:
                message = 'Inconsistent password.'
        return render(request, 'account/reset.html', {
            'reset_form': reset_form, 'message': message, 'updated': updated, 'is_valid': is_valid
        })

    reset_form = PasswordResetForm()
    return render(request, 'account/reset.html', {'reset_form': reset_form, 'is_valid': is_valid})


# 用户注销
def logout(request):
    # 删除 session 里的所有内容，此时需要再登录来更新 session 内容
    request.session.flush()
    return redirect('login')


# 标注平台主页，包含发布的所有标注任务
@require_login
def index(request):
    uid = request.session.get('uid')
    try:
        user = UserProfile.objects.get(uid=uid)
    except UserProfile.DoesNotExist:
        return Http404
    return render(request, 'index.html', {'user': user})


#####################################################################################################
# 论辩挖掘任务

# 论辩挖掘任务用户主页（包含用户申请的任务列表）
@require_login
def am(request):
    # 根据 session 信息获取用户 id
    uid = request.session.get('uid')
    user = UserProfile.objects.get(uid=uid)

    # 读取 Job 表
    sys_jobs = Job.objects.filter(uid=uid, job_type=0)
    free_jobs = Job.objects.filter(uid=uid, job_type=1)

    sys_annotateds, free_annotateds = [], []

    for job in sys_jobs:
        sys_annotateds.append(Annotated.objects.filter(job_id=job.job_id))

    for job in free_jobs:
        free_annotateds.append(Annotated.objects.filter(job_id=job.job_id))

    if request.method == 'POST':
        # 获取用户申请标注的文章数
        job_size = JOB_SIZE_DICT.get(request.POST.get('job_size'))
        # 根据用户申请标注的文章数分配文章
        status = assign(uid=uid, job_size=job_size, job_type=1, tested=False)
        message = JOB_APPLY_MESSAGE.get(status)
        # 根据申请任务返回的状态，渲染不同的网页
        if status == 4:
            return redirect('am')
        else:
            return render(request, 'annotation/argument_mining/list.html', {
                'user': user,
                'sys_jobs': zip(sys_jobs, sys_annotateds),
                'free_jobs': zip(free_jobs, free_annotateds),
                'message': message,
            })

    return render(request, 'annotation/argument_mining/list.html', {
        'user': user,
        'sys_jobs': zip(sys_jobs, sys_annotateds),
        'free_jobs': zip(free_jobs, free_annotateds),
    })


# 论辩挖掘任务标注详情
@require_login
def am_annotate(request, job_id, article_id):
    # 根据 session 信息获取用户 id
    uid = request.session.get('uid')
    user = UserProfile.objects.get(uid=uid)
    # 根据用户对任务id，获取用户的所有标注结果
    annotateds = Annotated.objects.filter(job_id=job_id)
    # 获取上一页和下一页的文章 id
    article_ids = [instance.id for instance in annotateds]

    # 上一页文章 id
    if article_ids.index(article_id) == 0:
        previous_article_id = None
    else:
        previous_article_id = article_ids[article_ids.index(article_id) - 1]
    # 下一页文章 id
    if article_ids.index(article_id) == len(article_ids) - 1:
        next_article_id = None
    else:
        next_article_id = article_ids[article_ids.index(article_id) + 1]

    # 根据用户的任务id 和 文章id，获取用户的标注结果
    try:
        annotated = annotateds.get(id=article_id)
    except Annotated.DoesNotExist:
        # 如果无过滤结果，说明文章id 和 任务id 不匹配
        raise Http404

    # 获取待标注文章具体信息
    try:
        article = Article.objects.get(id=annotated.id)
    except Article.DoesNotExist:
        raise Http404

    # 根据 job_id 获取用户当前任务的情况
    job = Job.objects.get(job_id=job_id)

    # 如果使用 post 提交数据
    if request.method == 'POST':

        print(request.POST)

        # 解析 POST 的数据
        arg_type, arg_rel, diff = \
            request.POST.getlist('arg_type'), request.POST.getlist('arg_rel'), request.POST.get('diff')

        # 数据类型转换
        if arg_type:
            arg_type = [int(item) for item in arg_type]
        if arg_rel:
            arg_rel = list(chunks([int(item) for item in arg_rel], chunk_size=3))
        if diff:
            diff = int(diff)

        # 用户提交的时间戳
        submitted_timestamp = timezone.now()
        annotated.duration = annotated.duration + (submitted_timestamp - annotated.visited).seconds
        annotated.visited = submitted_timestamp

        # 这里有 bug
        job.reward_progress += (1 - annotated.is_annotated) * article.get_price()

        # 更新任务状态
        if not annotated.is_annotated:
            job.job_progress += 1

        # 更新标注状态
        annotated.is_annotated = True
        annotated.annotated = json.dumps({'arg_type': arg_type, 'arg_rel': arg_rel, 'diff': diff})
        annotated.save()

        if job.job_progress == job.job_size:
            job.status = 1
            if not job.finished:
                job.finished = timezone.now()
        job.save()

        # 更新至数据库后，刷新当前页面
        return redirect(request.get_full_path())

    # 记录用户访问的时间戳
    annotated.visited = timezone.now()
    annotated.save()

    # 查看文章是否已被标注
    arg_type, arg_rel, diff = json.dumps(None), json.dumps(None), -1
    arg_type_real, arg_rel_real, exit_real = json.dumps(None), json.dumps(None), False
    if annotated.is_annotated:
        arg_type, arg_rel, diff = annotated.fetch_annotated()
        if Reviewed.objects.filter(id=annotated.id):
            arg_type_real, arg_rel_real = Reviewed.objects.get(id=annotated.id).fetch_annotated()
            exit_real = True

    return render(request, 'annotation/argument_mining/detail.html', {
        'user': user,
        'annotated': annotated,
        'annotateds': annotateds,
        'article': article,
        'arg_type': arg_type,
        'arg_rel': arg_rel,
        'diff': diff,
        'previous_article_id': previous_article_id,
        'next_article_id': next_article_id,
        'arg_type_real': arg_type_real,
        'arg_rel_real': arg_rel_real,
        'exit_real': exit_real,
    })


# 论辩挖掘任务审核用户主页
@require_login
def review(request):
    # 根据 session 信息获取用户 id
    uid = request.session.get('uid')
    user = UserProfile.objects.get(uid=uid)

    new_job_time = datetime.date(2020, 9, 10)

    # 计算 agreement (在这里可以过滤一些 agreement)
    annotateds = Annotated.objects.filter(
        job_id__in=[job.job_id for job in Job.objects.filter(
            is_expired=False,
            created__gt=new_job_time,
        )],
        is_annotated=True
    )

    # 计算 query 对应的 id
    id_to_annotateds = []
    for query in annotateds.values("id").annotate(count=Count("id")).order_by():
        if query.get('count') == MAX_ANNOTATED:
            _id = query.get('id')
            price = Article.objects.get(id=_id).get_review_price()
            cohen_kappa1 = agreement_arg_type(
                [annotated.arg_type_template() for annotated in annotateds.filter(id=_id)])
            cohen_kappa2 = agreement_arg_relation(
                [annotated.arg_rel_template() for annotated in annotateds.filter(id=_id)])
            id_to_annotateds.append([
                _id, cohen_kappa1, cohen_kappa2, (cohen_kappa1 + cohen_kappa2) / 2,
                True if Reviewed.objects.filter(id=_id) else False,
                1 if _id % 2 else 19, price,
            ])

    # 按照总的 Agreement 排序
    sorted_ids = sorted(id_to_annotateds, key=lambda d: d[3], reverse=False)

    if uid == 19:
        num_reviewed = 31 + len(Reviewed.objects.filter(uid=uid))
        pays = 185.25 + sum([Article.objects.get(
            id=reviewed.id).get_review_price() for reviewed in Reviewed.objects.filter(uid=uid)])
    else:
        num_reviewed = len(Reviewed.objects.filter(uid=uid))
        pays = sum([Article.objects.get(
            id=reviewed.id).get_review_price() for reviewed in Reviewed.objects.filter(uid=uid)])

    # num_reviewed = len(Reviewed.objects.filter(uid=uid))
    # pays = sum([Article.objects.get(
    #     id=reviewed.id).get_review_price() for reviewed in Reviewed.objects.filter(uid=uid)])

    return render(request, 'annotation/argument_mining/list_review.html', {
        'user': user,
        'sorted_ids': sorted_ids,
        'pays': pays,
        'num_reviewed': num_reviewed,
    })


# 论辩挖掘任务审核详细界面
@require_login
def review_detail(request, _id):
    # 根据 session 信息获取用户 id
    uid = request.session.get('uid')
    user = UserProfile.objects.get(uid=uid)

    annotateds = Annotated.objects.filter(
        job_id__in=[job.job_id for job in Job.objects.filter(is_expired=False)],
        is_annotated=True
    ).filter(id=_id)

    if not annotateds:
        raise Http404

    article = Article.objects.get(id=_id)

    arg_type = json.dumps([annotated.arg_type_template() for annotated in annotateds])
    arg_rel = [annotated.arg_rel_template() for annotated in annotateds]

    user_names = [
        UserProfile.objects.get(uid=Job.objects.get(job_id=annotated.job_id).uid).username for annotated in annotateds
    ]

    from collections import defaultdict
    d = defaultdict(list)
    for i, item in enumerate(arg_rel):
        for j in item:
            d[tuple(j)].append(user_names[i])

    result = []
    for key in d:
        a = list(key)
        a = [k + 1 for k in a]
        a.append('; '.join(d.get(key)))
        result.append(a)

    # 如果使用 post 提交数据
    if request.method == 'POST':

        # 解析 POST 的数据
        arg_type_p, arg_rel_p = request.POST.getlist('arg_type'), request.POST.getlist('arg_rel')

        # 数据类型转换
        if arg_type_p:
            arg_type_p = [int(item) for item in arg_type_p]
        if arg_rel_p:
            arg_rel_p = list(chunks([int(item) for item in arg_rel_p], chunk_size=3))

        Reviewed.objects.update_or_create(
            id=_id,
            uid=uid,
            defaults={
                'reviewed': json.dumps({'arg_type': arg_type_p, 'arg_rel': arg_rel_p}),
            }
        )

        # 更新至数据库后，刷新当前页面
        return redirect(request.get_full_path())

    arg_type_, arg_rel_ = [], []

    if Reviewed.objects.filter(id=_id):
        arg_type_, arg_rel_ = Reviewed.objects.get(id=_id).fetch_annotated()

    return render(request, 'annotation/argument_mining/detail_review.html', {
        'user': user,
        'user_names': user_names,
        'article': article,
        'arg_type': arg_type,
        'arg_type_': arg_type_,
        'arg_rel': json.dumps(arg_rel),
        'arg_rel_': arg_rel_,
        'result': result,
    })


# 标注教程
@require_login
def tutorial(request):
    # 根据 session 信息获取用户 id
    uid = request.session.get('uid')
    user = UserProfile.objects.get(uid=uid)

    return render(request, 'annotation/argument_mining/tutorial.html', {
        'user': user,
    })


# 视频教程
def video(request, name: str):
    # 根据 session 信息获取用户 id
    uid = request.session.get('uid')
    user = UserProfile.objects.get(uid=uid)
    return render(request, 'annotation/argument_mining/tutorial_video.html', {'user': user, 'name': name})


# 用户主页 home
@require_login
def home(request):
    # 根据 session 获取用户 id
    uid = request.session.get('uid')
    user = UserProfile.objects.get(uid=uid)
    # 过滤得到用户标注的列表
    annotateds = Annotated.objects.filter(
        job_id__in=[job.job_id for job in Job.objects.filter(uid=uid)])

    agreement_type, agreement_rel, is_reviewed = [], [], []
    for annotated in annotateds:
        if Reviewed.objects.filter(id=annotated.id):
            reviewed = Reviewed.objects.get(id=annotated.id)
            t1, t2 = parse_diff(annotated.annotated, reviewed.reviewed)
            agreement_type.append(t1)
            agreement_rel.append(t2)
            is_reviewed.append(True)
        else:
            agreement_type.append(None)
            agreement_rel.append(None)
            is_reviewed.append(False)

    return render(request, 'annotation/argument_mining/home.html', {
        'user': user,
        'annotateds': zip(annotateds, agreement_type, agreement_rel, is_reviewed),
    })


def parse_diff(label1, label2):
    arg_type1 = json.loads(label1).get('arg_type')
    arg_rel1 = json.loads(label1).get('arg_rel')
    arg_type2 = json.loads(label2).get('arg_type')
    arg_rel2 = json.loads(label2).get('arg_rel')
    return agreement_arg_type_double(arg_type1, arg_type2), agreement_arg_relation_double(arg_rel1, arg_rel2)


# 排行榜
@require_login
def leaderboard(request):
    # 根据 session 信息获取用户 id
    uid = request.session.get('uid')
    user_ = UserProfile.objects.get(uid=uid)
    records = []
    for user in UserProfile.objects.all():
        jobs = Job.objects.filter(uid=user.uid, is_expired=False)
        if jobs:
            record = jobs.aggregate(
                num_jobs=Count('*'),
                num_instances=Sum('job_size'),
                num_annotated_instances=Sum('job_progress'),
                reward=Sum('reward_progress'))
            record['username'] = user.username
            record['uid'] = user.uid
            record['role'] = user.role
            record['created'] = user.created
            annotateds = Annotated.objects.filter(job_id__in=[job.job_id for job in jobs], is_annotated=True)
            if annotateds:
                record['duration'] = annotateds.aggregate(duration=Sum('duration')).get('duration') / 3600
            else:
                record['duration'] = 0.0
            records.append(record)

    return render(request, 'annotation/argument_mining/leaderboard.html', {
        'user': user_,
        'records': sorted(records, key=lambda x: x.get('reward'), reverse=True),
    })


# FAQ
@require_login
def faq(request):
    # 根据 session 信息获取用户 id
    uid = request.session.get('uid')
    user = UserProfile.objects.get(uid=uid)
    return render(request, 'annotation/argument_mining/faq.html', {'user': user})


# 标注团队信息
@require_login
def about_me(request):
    # 根据 session 信息获取用户 id
    uid = request.session.get('uid')
    user = UserProfile.objects.get(uid=uid)
    # 首页中关于标准团队的信息
    return render(request, 'annotation/argument_mining/about.html', {'user': user})


# 论辩挖掘任务审核用户主页
@require_login
def cl_review(request):
    # 根据 session 信息获取用户 id
    uid = request.session.get('uid')
    user = UserProfile.objects.get(uid=uid)
    # 首页中关于标准团队的信息
    return render(request, 'annotation/argument_mining/cl_review.html', {'user': user})
#####################################################################################################
