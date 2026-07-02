from app.services.complaint_service import ComplaintClassifier
import pytest


@pytest.fixture
def classifier():
    return ComplaintClassifier()


def test_classify_officer_misconduct(classifier):
    result = classifier._rule_based_classify("The officer demanded bribe for issuing certificate")
    assert result["category"] == "officer_misconduct"
    assert result["urgency_score"] >= 7.0


def test_classify_urgent(classifier):
    result = classifier._rule_based_classify("My child's exam is tomorrow and certificate not issued URGENT")
    assert result["category"] == "urgent_grievance"


def test_classify_portal(classifier):
    result = classifier._rule_based_classify("Getting error 500 while uploading on portal")
    assert result["category"] == "portal_technical"


def test_hindi_bribe(classifier):
    result = classifier._rule_based_classify("अधिकारी ने रिश्वत मांगी")
    assert result["category"] == "officer_misconduct"


def test_sla_risk_keys(classifier):
    result = classifier.classify("My certificate is pending for weeks")
    assert result["sla_risk"] in ["low", "medium", "high"]


def test_urgency_range(classifier):
    result = classifier.classify("Certificate pending for 2 weeks")
    assert 0.0 <= result["urgency_score"] <= 10.0


def test_detect_hindi(classifier):
    assert classifier.detect_language("मेरा प्रमाण पत्र लंबित है") == "hi"
