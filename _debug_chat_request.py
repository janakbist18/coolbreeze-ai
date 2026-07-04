import json
import os
import traceback

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dj_ai_employee_main.settings")

import django

django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from orders.models import Order

User = get_user_model()
u = User.objects.get(username="techwithrathan")
o = Order.objects.filter(user=u).first()

c = Client()
c.force_login(u)

try:
    response = c.post(
        f"/support/chat/{o.id}/",
        data=json.dumps({"message": "Hii"}),
        content_type="application/json",
    )
    print("status", response.status_code)
    print(response.content.decode())
except Exception as exc:
    print(type(exc).__name__, exc)
    traceback.print_exc()
