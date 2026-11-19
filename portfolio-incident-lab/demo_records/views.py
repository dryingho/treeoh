from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import DemoCustomer


# 가상 고객 목록 (운영자만 볼 수 있음)
@login_required
def record_list(request):
    return render(request, "demo_records/list.html", {"customers": DemoCustomer.objects.all()})
