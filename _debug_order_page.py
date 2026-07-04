import os
import traceback

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dj_ai_employee_main.settings")

import django

django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from orders.models import Order

User = get_user_model()
u = User.objects.get(username="techwithrathan")
o = Order.objects.filter(user=u).first()

c = Client()
c.force_login(u)

try:
    response = c.get(f"/orders/{o.id}/")
    print("status", response.status_code)
    print(response.content.decode()[:4000])
except Exception as exc:
    print(type(exc).__name__, exc)
    traceback.print_exc()
