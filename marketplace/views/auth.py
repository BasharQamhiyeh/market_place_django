import logging
import re
from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout

from marketplace.forms import UserRegistrationForm, SignupAfterOtpForm, ForgotPasswordForm, PhoneVerificationForm, \
    ResetPasswordForm
from marketplace.models import User, Store, SiteSettings
from marketplace.services.notifications import notify, S_REWARD, K_WALLET
from marketplace.services.wallet import earn_points
from marketplace.utils.sms import send_sms_code
from marketplace.utils.verification import send_code, verify_session_code
from marketplace.views.helpers import _phone_candidates

logger = logging.getLogger(__name__)


def register(request):
    """
    Render the SINGLE-PAGE mockup UI.
    (No user creation here.)
    """
    # capture referral if present
    ref_code = request.GET.get("ref")
    if ref_code:
        request.session["ref_code"] = ref_code

    form = UserRegistrationForm()
    return render(request, "register.html", {"form": form})


@require_POST
@csrf_protect
def ajax_send_signup_otp(request):
    """
    Mockup Step 1:
    - receive phone only
    - normalize
    - check not registered
    - send_code(...)
    - store pending phone in session
    """
    phone = (request.POST.get("phone") or "").strip().replace(" ", "").replace("-", "")

    # ✅ ONLY allow 07########
    if not re.fullmatch(r"07\d{8}", phone):
        return JsonResponse(
            {"ok": False, "error": "رقم الهاتف يجب أن يبدأ بـ 07 ويتكون من 10 أرقام. مثال: 0790000000"},
            status=400
        )

    # ✅ canonical format saved/used by OTP: 9627xxxxxxxx
    phone_norm = "962" + phone[1:]  # 9627xxxxxxxx

    # ✅ robust duplicate check (in case DB has old formats)
    local07 = phone  # 07xxxxxxxx
    plus = "+" + phone_norm  # +9627xxxxxxxx
    zerozero = "00" + phone_norm  # 009627xxxxxxxx

    if User.objects.filter(Q(phone=phone_norm) | Q(phone=local07) | Q(phone=plus) | Q(phone=zerozero)).exists():
        return JsonResponse(
            {"ok": False, "duplicated": True, "error": "هذا الرقم مسجَّل لدينا بالفعل."},
            status=409
        )

    request.session["pending_phone"] = phone_norm
    request.session["phone_verified_ok"] = False

    send_code(request, phone_norm, "verification", "verify", send_sms_code)
    return JsonResponse({"ok": True})


@require_POST
@csrf_protect
def ajax_verify_signup_otp(request):
    """
    Mockup Step 2 (popup):
    - verify code using verify_session_code
    - mark session verified
    """
    pending_phone = request.session.get("pending_phone")
    if not pending_phone:
        return JsonResponse({"ok": False, "error": "انتهت الجلسة. يرجى إعادة المحاولة."}, status=400)

    code = (request.POST.get("code") or "").strip()
    if not code:
        return JsonResponse({"ok": False, "error": "أدخل رمز التحقق."}, status=400)

    if not verify_session_code(request, "verification", code):
        return JsonResponse({"ok": False, "error": "⚠️ الرمز غير صحيح أو منتهي الصلاحية."}, status=400)

    request.session["phone_verified_ok"] = True
    return JsonResponse({"ok": True, "phone": pending_phone})


@csrf_protect
def complete_signup(request):
    if request.method != "POST":
        return redirect("register")

    pending_phone = request.session.get("pending_phone")
    verified_ok = request.session.get("phone_verified_ok", False)
    if not pending_phone or not verified_ok:
        messages.error(request, "يرجى تأكيد رقم الهاتف أولاً.")
        return redirect("register")

    # ✅ IMPORTANT for store_logo
    form = SignupAfterOtpForm(request.POST, request.FILES)

    if not form.is_valid():
        return render(request, "register.html", {
            "signup_form": form,
            "restore_step": "details",
            "verified_phone": pending_phone,
        })

    # safety re-check (handle old formats too)
    local07 = "0" + pending_phone[3:]     # 07xxxxxxxx
    plus = "+" + pending_phone            # +9627xxxxxxxx
    zerozero = "00" + pending_phone       # 009627xxxxxxxx

    if User.objects.filter(Q(phone=pending_phone) | Q(phone=local07) | Q(phone=plus) | Q(phone=zerozero)).exists():
        messages.error(request, "هذا الرقم مسجَّل لدينا بالفعل.")
        return redirect("register")

    with transaction.atomic():
        user = User.objects.create_user(
            phone=pending_phone,
            password=form.cleaned_data["password"],
        )

        user.first_name = form.cleaned_data.get("first_name", "") or ""
        user.last_name = form.cleaned_data.get("last_name", "") or ""
        user.is_active = True
        user.show_phone = True

        # ⚠️ only keep this if the field exists in your User model
        if hasattr(user, "phone_verified"):
            user.phone_verified = True

        if getattr(user, "date_joined", None) is None:
            user.date_joined = timezone.now()

        # referral
        ref_code = request.session.get("ref_code")
        if ref_code:
            try:
                referrer = User.objects.get(referral_code=ref_code)
                user.referred_by = referrer
            except User.DoesNotExist:
                pass

        user.save()

        # ✅ store creation
        if form.cleaned_data.get("condition") == "store":
            Store.objects.create(
                owner=user,
                name=form.cleaned_data.get("store_name", "").strip(),
                logo=form.cleaned_data.get("store_logo"),
            )

        site = SiteSettings.get()

        # ✅ Registration bonus for the new user
        if site.registration_points > 0:
            earn_points(
                user=user,
                amount=site.registration_points,
                reason="registration_bonus",
                meta={"points": site.registration_points},
            )

        # ✅ Referral reward for the inviter
        if user.referred_by:
            earn_points(
                user=user.referred_by,
                amount=site.referral_points,
                reason="referral_reward",
                meta={
                    "action": "invite",
                    "targetType": "user",
                    "id": user.user_id,
                    "title": f"{user.first_name} {user.last_name}".strip() or user.phone,
                    "points": site.referral_points,
                },
            )

            notify(
                user=user.referred_by,
                kind=K_WALLET,
                status=S_REWARD,
                title="مكافأة دعوة صديق",
                body=f"حصلت على +{site.referral_points} نقطة لأن صديقك سجّل عبر رابطك.",
            )

    # cleanup
    for key in ["pending_phone", "phone_verified_ok", "verification_code", "verification_sent_at", "ref_code"]:
        request.session.pop(key, None)

    login(request, user)
    messages.success(request, "✅ تم إنشاء الحساب بنجاح!")
    return redirect("home")


def user_login(request):
    if request.method != "POST":
        return redirect("/")

    raw = (request.POST.get("username") or "").strip()
    password = request.POST.get("password") or ""
    referer = request.META.get("HTTP_REFERER", "/")
    next_url = (request.POST.get("next") or request.GET.get("next") or "").strip()

    def redirect_login_error():
        # keep next so after user fixes password, we still go to create page
        suffix = "?login_error=1"
        if next_url:
            suffix += f"&next={next_url}"
        return redirect(f"{referer}{suffix}")

    candidates = _phone_candidates(raw)

    if not candidates:
        return redirect_login_error()

    u = User.objects.filter(phone__in=candidates).first()
    if not u:
        return redirect_login_error()

    # Authenticate using the model's USERNAME_FIELD (works for custom User models)
    login_key = User.USERNAME_FIELD
    login_val = getattr(u, login_key, None)

    user = authenticate(request, password=password, **{login_key: login_val})

    if not user:
        logger.warning("Failed login attempt for phone candidates: %s", candidates)
        return redirect_login_error()

    login(request, user)
    logger.info("Successful login for user %s", user.pk)

    # ✅ redirect to next (create item/request) if provided and safe
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)

    # fallback
    return redirect(referer)


def user_logout(request):
    logout(request)
    return redirect('home')


def forgot_password(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            try:
                user = User.objects.get(phone=phone)
            except User.DoesNotExist:
                messages.error(request, "❌ رقم الهاتف غير موجود.")
                return redirect('forgot_password')

            # rate limit: 1 minute
            last_sent = request.session.get('reset_sent_at')
            if last_sent and timezone.now() - timezone.datetime.fromisoformat(last_sent) < timedelta(minutes=1):
                messages.warning(request, "⚠️ يرجى الانتظار دقيقة قبل طلب رمز جديد.")
                return redirect('forgot_password')

            send_code(request, phone, "reset", "reset", send_sms_code)
            request.session['reset_phone'] = phone
            messages.info(request, "📱 تم إرسال رمز التحقق إلى رقم هاتفك.")
            return redirect('verify_reset_code')
    else:
        form = ForgotPasswordForm()

    return render(request, 'forgot_password.html', {'form': form})


def verify_reset_code(request):
    phone = request.session.get('reset_phone')
    if not phone:
        messages.error(request, "انتهت الجلسة. يرجى إعادة المحاولة.")
        return redirect('forgot_password')

    if request.method == 'POST':
        form = PhoneVerificationForm(request.POST)
        if form.is_valid():
            entered_code = form.cleaned_data['code']
            if verify_session_code(request, "reset", entered_code):
                request.session['reset_verified'] = True
                messages.success(request, "✅ تم التحقق من الرمز. يمكنك الآن تعيين كلمة مرور جديدة.")
                return redirect('reset_password')
            else:
                messages.error(request, "⚠️ الرمز غير صحيح أو منتهي الصلاحية.")
    else:
        form = PhoneVerificationForm()

    return render(request, 'verify_reset_code.html', {'form': form, 'phone': phone})


def reset_password(request):
    if not request.session.get('reset_verified'):
        messages.error(request, "يرجى التحقق من الرمز أولاً.")
        return redirect('forgot_password')

    phone = request.session.get('reset_phone')
    if not phone:
        messages.error(request, "حدث خطأ. يرجى إعادة المحاولة.")
        return redirect('forgot_password')

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            confirm_password = form.cleaned_data['confirm_password']

            if new_password != confirm_password:
                messages.error(request, "⚠️ كلمتا المرور غير متطابقتين.")
                return redirect('reset_password')

            try:
                user = User.objects.get(phone=phone)
                user.password = make_password(new_password)
                user.save()

                # clear session data
                for key in ['reset_phone', 'reset_code', 'reset_sent_at', 'reset_verified']:
                    request.session.pop(key, None)

                messages.success(request, "✅ تم تعيين كلمة المرور الجديدة بنجاح. يمكنك تسجيل الدخول الآن.")
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, "حدث خطأ. يرجى إعادة المحاولة.")
    else:
        form = ResetPasswordForm()

    return render(request, 'reset_password.html', {'form': form})