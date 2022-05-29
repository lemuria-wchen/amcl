from django.core.mail import send_mail

from ..models import EmailVerifyRecord
from amcl.settings import EMAIL_FROM
import uuid


IP_ADDR = '127.0.0.1'
PORT = '8888'


def create_uid() -> str:
    return str(uuid.uuid1())


def get_id_addr():
    return 'http://{}:{}'.format(IP_ADDR, PORT)


# 发送账号验证或密码修改邮件
def send_register_email(user, send_type='register'):

    assert send_type in ['register', 'reset'], 'send_type must be either \'register\' or \'reset\'.'

    # 随机生成一串激活码
    captcha = create_uid()

    # ip 地址（项目部署的地址）
    ip_addr = get_id_addr()

    if send_type == 'register':
        # 新注册账号激活邮件
        title = 'Activate your account ｜ FNLP-DISC Data Annotation Team'
        body = 'Hello {}! Please click the link below to activate your account: \n\t' \
               '{}/annotation/activate/{}'.format(user.username, ip_addr, captcha)
        status = send_mail(subject=title, message=body, from_email=EMAIL_FROM, recipient_list=[user.email, ])
    else:
        # 密码重置邮件
        title = 'Reset your password ｜ FNLP-DISC Data Annotation Team'
        body = 'Hello {}! Please click the link below to reset your password: \n\t' \
               '{}/annotation/reset/{}'.format(user.username, ip_addr, captcha)
        status = send_mail(subject=title, message=body, from_email=EMAIL_FROM, recipient_list=[user.email, ])

    if status:
        # 如果邮件发送成功，则保存邮件发送记录
        EmailVerifyRecord.objects.create(uid=user.uid, captcha=captcha, is_valid=True, send_type=send_type)

    return status
