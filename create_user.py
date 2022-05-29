import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'amcl.settings')
django.setup()

from annotation.models import UserProfile
from django.contrib.auth.hashers import make_password


# create an annotator
UserProfile(
  email='test1@fudan.edu.cn', student_id='test1', name='test1', username='test1', gender=0,
  phone_number=15071320287, education=1, school=0, password=make_password('test1'),
  role=2).save()

# create a reviewer
UserProfile(
  email='test2@fudan.edu.cn', student_id='test2', name='test2', username='test2', gender=0,
  phone_number=15071320287, education=1, school=0, password=make_password('test2'),
  role=3).save()

