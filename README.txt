Stripe patch contents

Replace directly:
- models.py
- auth_service.py
- app/templates/pricing.html
- app/static/pricing.js

Add new:
- stripe_service.py

Paste into your main FastAPI file:
- main_stripe_patch.py

Add dependency:
- requirements_addition.txt
