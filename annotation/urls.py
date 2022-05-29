from django.urls import path
from .views import index, login, register, activate, forget, reset, logout
from .views import about_me, am, am_annotate, leaderboard, faq, home, tutorial, review, review_detail, video, cl_review

urlpatterns = [

    # account
    path('login', login, name='login'),  # 登录界面
    path('register', register, name='register'),  # 注册界面
    path('activate/<str:captcha>', activate, name='activate'),  # 激活邮件界面
    path('forget', forget, name='forget'),  # 忘记密码界面
    path('reset/<str:captcha>', reset, name='reset'),  # 重置密码界面
    path('logout', logout, name='logout'),  # 登出界面

    # annotation publishing platform
    path('', index, name='index'),  # 标注任务发布主页，标注任务可以在这里更新和发布

    # annotation homepage
    path('am', am, name='am'),  # 论辩挖掘任务标注主页
    # annotation detail
    path('am/<int:job_id>/<int:article_id>', am_annotate, name='am_annotate'),  # 论辩挖掘标注任务详情界面

    # user homepage
    path('am/home', home, name='home'),  # 用户主页

    path('am/leaderboard', leaderboard, name='leaderboard'),
    path('am/faq', faq, name='faq'),
    path('am/about', about_me, name='about'),
    path('am/tutorial', tutorial, name='tutorial'),
    path('am/tutorial/video/<str:name>', video, name='video'),
    path('am/cl_review', cl_review, name='cl_review'),

    # review homepage
    path('am/review', review, name='review'),  # 审核界面
    # review detail
    path('am/review/<int:_id>', review_detail, name='review_detail'),  # 审核界面详情

]
