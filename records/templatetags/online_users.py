# records/templatetags/online_users.py
from django import template
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

register = template.Library()

@register.inclusion_tag('records/tags/online_user_list.html')
def online_user_list():
    # 5분 전 시간을 계산
    five_minutes_ago = timezone.now() - timedelta(minutes=5)
    
    # 최근 5분 이내에 활동한 사용자를 조회
    online_users = User.objects.filter(profile__last_seen__gte=five_minutes_ago)
    
    return {'online_users': online_users}