from django.contrib import admin
from .models import Article, Citation, UserProfile, Annotated, Job, EmailVerifyRecord, Reviewed


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('id', 'doi', 'title', 'au', 'year',
                    'cited', 'citing', 'journal', 'num_segments', 'topic_id', 'version')
    search_fields = ('id',)


@admin.register(Citation)
class CitationAdmin(admin.ModelAdmin):
    list_display = ('cite', 'cited')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'uid', 'email', 'student_id', 'username', 'name', 'phone_number', 'gender',
        'education', 'school', 'role', 'created', 'updated'
    )
    date_hierarchy = 'created'


@admin.register(EmailVerifyRecord)
class EmailVerifyRecordAdmin(admin.ModelAdmin):
    list_display = ('uid', 'captcha', 'is_valid', 'send_type', 'send_time')
    date_hierarchy = 'send_time'


@admin.register(Annotated)
class AnnotatedAdmin(admin.ModelAdmin):
    list_display = ('job_id', 'id', 'annotated', 'is_annotated', 'visited', 'duration')
    search_fields = ('id',)


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        'job_id', 'uid', 'job_progress', 'job_size', 'reward_progress', 'reward',
        'status', 'job_type', 'created', 'finished', 'expired', 'is_expired'
    )


@admin.register(Reviewed)
class ReviewedAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'reviewed',
    )
