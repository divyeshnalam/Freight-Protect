from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.staticfiles import finders
from email.mime.image import MIMEImage
import os, json, requests

RECAPTCHA_SECRET_KEY = "6LfCnXMrAAAAALB_8EBx_8cpMbw1JAhlofoysJcS"

def index(request):
    return render(request, "website/index.html")

def contact(request):
    return render(request, "website/contact.html")

def verify_recaptcha(token):
    url = "https://www.google.com/recaptcha/api/siteverify"
    data = {'secret': RECAPTCHA_SECRET_KEY, 'response': token}
    try:
        response = requests.post(url, data=data)
        result = response.json()
        return result.get('success', False)
    except Exception:
        return False

@csrf_exempt
def contact_submit(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode("utf-8"))

            recaptcha_token = data.get('recaptcha', '')
            if not recaptcha_token or not verify_recaptcha(recaptcha_token):
                return JsonResponse({'success': False, 'error': 'Invalid reCAPTCHA'}, status=400)

            first_name = data.get('firstName', '').strip()
            last_name = data.get('lastName', '').strip()
            company_name = data.get('companyName', '').strip()
            work_email = data.get('workEmail', '').strip()
            mobile_phone = data.get('mobilePhone', '').strip()
            company_types = ', '.join(data.get('companyTypes', []))

            # === ADMIN EMAIL (inquiry notification) ===
            subject = f"LTL Inquiry – New Lead from {company_name or 'Unknown Company'}"
            plain_message = f"""
New LTL Sales Lead from Freight Protect

Name: {first_name} {last_name}
Company: {company_name}
Email: {work_email}
Phone: {mobile_phone}
Company Type: {company_types}

This lead has expressed interest in early access to Freight Protect's platform for LTL services.
Please follow up with them promptly.

---
This is an automated message from freightprotect.com
            """.strip()

            html_content = render_to_string('website/contact_email.html', {
                'first_name': first_name,
                'last_name': last_name,
                'company_name': company_name,
                'work_email': work_email,
                'mobile_phone': mobile_phone,
                'company_types': company_types,
            })

            email = EmailMultiAlternatives(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                ['lobanabalwan@gmail.com'],
            )
            email.attach_alternative(html_content, "text/html")

            logo_path = finders.find('website/img/Freight Protect.png')
            if not logo_path:
                return JsonResponse({'success': False, 'error': 'Logo image not found.'}, status=500)

            with open(logo_path, 'rb') as f:
                logo = MIMEImage(f.read())
                logo.add_header('Content-ID', '<freight_logo>')
                logo.add_header('Content-Disposition', 'inline', filename='Freight Protect.png')
                email.attach(logo)

            email.send()

            # === USER CONFIRMATION EMAIL ===
            confirmation_subject = "Thank you for contacting FreightProtect"
            confirmation_plain = f"""Hi {first_name},

Thank you for your interest in FreightProtect! We have received your request and will be in touch soon.

Here is what you submitted:
Name: {first_name} {last_name}
Company: {company_name}
Phone: {mobile_phone}
Email: {work_email}
Company Type: {company_types}

If anything is incorrect, reply to this email.

Best regards,
The FreightProtect Team

---
This is an automated message from freightprotect.com
"""

            confirmation_html = render_to_string('website/contact_confirmation_email.html', {
                'first_name': first_name,
                'last_name': last_name,
                'company_name': company_name,
                'work_email': work_email,
                'mobile_phone': mobile_phone,
                'company_types': company_types,
            })

            confirmation_email = EmailMultiAlternatives(
                confirmation_subject,
                confirmation_plain,
                settings.DEFAULT_FROM_EMAIL,
                [work_email],
            )
            confirmation_email.attach_alternative(confirmation_html, "text/html")

            # Attach the same logo for inline use:
            with open(logo_path, 'rb') as f:
                logo2 = MIMEImage(f.read())
                logo2.add_header('Content-ID', '<freight_logo>')
                logo2.add_header('Content-Disposition', 'inline', filename='Freight Protect.png')
                confirmation_email.attach(logo2)

            confirmation_email.send()

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)