from django.shortcuts import redirect, render

from chat.profiles import PATIENT_PROFILES


def entry_point(request):
    if request.method == "POST":
        # if request.POST.get("login__type") == "staff":
        #     return redirect("staff_dashboard")

        patient_type = request.POST.get("patient_type")
        if patient_type:
            request.session["patient_type"] = patient_type
            request.session.pop("chat_session_id", None)
            return redirect("chat_window")

    request.session.pop("chat_session_id", None)
    request.session.pop("patient_type", None)
    return render(request, "entry_point.html", {"patients": PATIENT_PROFILES.values()})
