"""Run: python ml/data/generate_complaints.py"""
import json, random, os

COMPLAINTS = {
    "certificate_delay": {"department": "Revenue Department", "sla_days": 7, "samples_en": [
        "My caste certificate application has been pending for 3 weeks. No response from the office.",
        "Applied for income certificate 15 days ago. Status still shows pending.",
        "Birth certificate not issued even after 20 days. Very urgent needed for school admission.",
        "My domicile certificate application submitted last month, no update yet.",
        "Certificate delayed beyond SLA period. Officer not responding to calls.",
        "Applied online for caste certificate 10 days back, no acknowledgment received.",
        "Income certificate application rejected without explanation, need help.",
        "Death certificate not processed even after 25 days of submission."],
        "samples_hi": ["मेरा जाति प्रमाण पत्र 3 हफ्तों से लंबित है। कार्यालय से कोई जवाब नहीं।",
        "आय प्रमाण पत्र के लिए 15 दिन पहले आवेदन किया था। स्थिति अभी भी लंबित है।",
        "जन्म प्रमाण पत्र 20 दिन बाद भी जारी नहीं हुआ। स्कूल प्रवेश के लिए जरूरी है।",
        "पिछले महीने अधिवास प्रमाण पत्र के लिए आवेदन किया, कोई अपडेट नहीं।",
        "प्रमाण पत्र SLA अवधि से अधिक देर हो गई। अधिकारी फोन नहीं उठा रहे।"]},
    "officer_misconduct": {"department": "Vigilance Department", "sla_days": 3, "samples_en": [
        "Officer demanded bribe for certificate issuance. This is corruption.",
        "The clerk at the counter was rude and refused to accept my application.",
        "Government employee asked for unofficial payment to process my documents.",
        "Officer at tehsil office misbehaved with my elderly mother during visit.",
        "Staff member threatened to reject application if payment not made.",
        "Officer deliberately delaying my file and demanding money.",
        "The verifying officer is not available during office hours."],
        "samples_hi": ["अधिकारी ने प्रमाण पत्र जारी करने के लिए रिश्वत मांगी। यह भ्रष्टाचार है।",
        "काउंटर पर क्लर्क अभद्र था और मेरा आवेदन स्वीकार करने से इनकार कर दिया।",
        "सरकारी कर्मचारी ने दस्तावेज़ संसाधित करने के लिए अनौपचारिक भुगतान मांगा।",
        "तहसील कार्यालय में अधिकारी ने मेरी बुजुर्ग माँ के साथ दुर्व्यवहार किया।"]},
    "wrong_information": {"department": "Revenue Department", "sla_days": 5, "samples_en": [
        "Name is misspelled in the issued certificate. Need correction urgently.",
        "Date of birth is wrong in my birth certificate. Please correct it.",
        "Address mentioned in domicile certificate is incorrect.",
        "Father's name is wrong in the caste certificate issued to me.",
        "Certificate has wrong district name. It should be Noida not Ghaziabad.",
        "Income amount mentioned is incorrect in my income certificate."],
        "samples_hi": ["जारी प्रमाण पत्र में नाम की गलत वर्तनी है। तत्काल सुधार चाहिए।",
        "मेरे जन्म प्रमाण पत्र में जन्म तिथि गलत है। कृपया सुधारें।",
        "निवास प्रमाण पत्र में उल्लिखित पता गलत है।"]},
    "portal_technical": {"department": "IT Department", "sla_days": 2, "samples_en": [
        "Unable to upload documents on the portal. Getting error 500.",
        "OTP not received on registered mobile number during login.",
        "Application form not submitting after filling all details.",
        "Portal showing session expired every time I try to apply.",
        "Payment gateway failing during fee submission.",
        "Downloaded certificate has blank fields. Generation error.",
        "Cannot log in to citizen portal. Password reset not working.",
        "Application tracking number not working on status check page."],
        "samples_hi": ["पोर्टल पर दस्तावेज़ अपलोड नहीं हो रहे। 500 त्रुटि आ रही है।",
        "लॉगिन के दौरान पंजीकृत मोबाइल नंबर पर OTP प्राप्त नहीं हुआ।",
        "सभी विवरण भरने के बाद आवेदन पत्र सबमिट नहीं हो रहा।"]},
    "document_rejection": {"department": "Revenue Department", "sla_days": 5, "samples_en": [
        "Application rejected without giving proper reason. Need explanation.",
        "Documents rejected saying they are not clear but they are perfectly fine.",
        "My application was rejected 3 times for different reasons each time.",
        "Rejection reason cited is wrong. Officer did not check documents properly.",
        "Application rejected for missing document that was clearly uploaded."],
        "samples_hi": ["उचित कारण बताए बिना आवेदन अस्वीकार किया गया। स्पष्टीकरण चाहिए।",
        "दस्तावेज़ अस्पष्ट कहकर अस्वीकार किए गए लेकिन वे बिल्कुल ठीक हैं।"]},
    "scheme_information": {"department": "Welfare Department", "sla_days": 10, "samples_en": [
        "Need information about eligibility criteria for PM Awas Yojana.",
        "How to apply for widow pension scheme? What documents needed?",
        "What is the income limit for OBC scholarship?",
        "How long does it take to receive disability certificate benefits?",
        "Need details about Ration card application process."],
        "samples_hi": ["PM आवास योजना के लिए पात्रता मानदंड के बारे में जानकारी चाहिए।",
        "विधवा पेंशन योजना के लिए आवेदन कैसे करें? कौन से दस्तावेज़ चाहिए?",
        "OBC छात्रवृत्ति के लिए आय सीमा क्या है?"]},
    "urgent_grievance": {"department": "Collector Office", "sla_days": 1, "samples_en": [
        "My child's school admission will be cancelled tomorrow without certificate. URGENT.",
        "Hospital refusing treatment without income certificate. Life at risk.",
        "Court hearing tomorrow, need certified copy of document TODAY.",
        "Passport application deadline today, certificate not issued.",
        "Child cannot appear in exam without birth certificate. Exam is tomorrow."],
        "samples_hi": ["प्रमाण पत्र के बिना कल मेरे बच्चे का स्कूल प्रवेश रद्द हो जाएगा। अत्यावश्यक।",
        "अस्पताल आय प्रमाण पत्र के बिना इलाज से मना कर रहा है। जीवन खतरे में।",
        "कल अदालत की सुनवाई, आज दस्तावेज़ की प्रमाणित प्रति चाहिए।"]},
}

URGENCY_MAP = {"certificate_delay": (4,7), "officer_misconduct": (7,10), "wrong_information": (3,6),
               "portal_technical": (2,5), "document_rejection": (3,6), "scheme_information": (1,3), "urgent_grievance": (8,10)}


def generate_dataset(samples_per_class=60):
    dataset = []
    for category, data in COMPLAINTS.items():
        all_samples = data["samples_en"] + data["samples_hi"]
        umin, umax = URGENCY_MAP[category]
        for _ in range(samples_per_class):
            text = random.choice(all_samples)
            urgency = round(random.uniform(umin, umax), 1)
            dataset.append({"text": text, "category": category, "department": data["department"],
                "urgency_score": urgency, "sla_days": data["sla_days"], "sla_breach_risk": urgency > 6.0,
                "language": "hi" if any(ord(c) > 2304 for c in text) else "en"})
    random.shuffle(dataset)
    return dataset


if __name__ == "__main__":
    os.makedirs("ml/data/processed", exist_ok=True)
    dataset = generate_dataset(60)
    with open("ml/data/processed/complaints.json", "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    print(f"Generated {len(dataset)} samples")
