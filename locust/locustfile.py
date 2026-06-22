from __future__ import annotations

import random
import uuid
from collections import deque
from typing import Any

from locust import HttpUser, between, task


PENDING_REVIEW_IDS: deque[str] = deque(maxlen=500)


STANDARD_WAIT = between(1, 5)


def _unique_ticket_id() -> int:
    return random.randint(100_000, 999_999)


def _unique_order_id(prefix: str = "ORD") -> str:
    return f"{prefix}-{random.randint(10000, 99999)}"


def _email() -> str:
    return f"load-{uuid.uuid4().hex[:10]}@example.com"


def _remember_pending_review(payload: dict[str, Any]) -> None:
    thread_id = payload.get("thread_id")
    if payload.get("status") == "pending_review" and thread_id:
        PENDING_REVIEW_IDS.append(thread_id)


def _remember_review_list(payload: dict[str, Any]) -> None:
    for review in payload.get("reviews", []):
        thread_id = review.get("thread_id")
        if thread_id:
            PENDING_REVIEW_IDS.append(thread_id)


class ComplaintForgeUser(HttpUser):
    wait_time = STANDARD_WAIT

    @task(15)
    def scenario_01_health_check(self) -> None:
        self._get_expected("/health", "01 health check", expected_status=200, json_field=("status", "healthy"))

    @task(3)
    def scenario_02_openapi_schema(self) -> None:
        self._get_expected("/openapi.json", "02 openapi schema", expected_status=200)

    @task(2)
    def scenario_03_docs_page(self) -> None:
        self._get_expected("/docs", "03 docs page", expected_status=200)

    @task(8)
    def scenario_04_list_pending_reviews(self) -> None:
        with self.client.get("/review", name="04 list pending reviews", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Expected 200, got {response.status_code}")
                return
            _remember_review_list(response.json())

    @task(4)
    def scenario_05_get_pending_review_detail(self) -> None:
        thread_id = self._next_pending_review_id()
        if not thread_id:
            return
        self._get_expected(f"/review/{thread_id}", "05 get pending review detail", expected_status={200, 404})

    @task(3)
    def scenario_06_get_unknown_review_detail(self) -> None:
        self._get_expected(f"/review/{uuid.uuid4()}", "06 get unknown review detail", expected_status=404)

    @task(2)
    def scenario_07_resume_review_approved(self) -> None:
        thread_id = self._pop_pending_review_id()
        if not thread_id:
            return
        self._post_review_resume(thread_id, {
            "approved": True,
            "notes": "Approved during Locust load scenario.",
            "final_response": "Thanks for your patience. We reviewed your case and approved the next support action.",
        }, "07 resume review approved")

    @task(2)
    def scenario_08_resume_review_adjusted_resolution(self) -> None:
        thread_id = self._pop_pending_review_id()
        if not thread_id:
            return
        self._post_review_resume(thread_id, {
            "approved": True,
            "notes": "Approved partial refund after load-test review.",
            "resolution": {
                "resolution_type": "partial_refund",
                "refund_amount": 75,
                "credit_amount": 0,
                "action_needed": "Create refund workflow case in Salesforce",
                "confidence": 0.95,
            },
            "final_response": "Thanks for your patience. We reviewed your case and approved a partial refund.",
        }, "08 resume review adjusted resolution")

    @task(1)
    def scenario_09_resume_review_rejected(self) -> None:
        thread_id = self._pop_pending_review_id()
        if not thread_id:
            return
        self._post_review_resume(thread_id, {
            "approved": False,
            "notes": "Rejected during Locust load scenario for additional review.",
            "final_response": "Thanks for your patience. Our support team is continuing to review your case.",
        }, "09 resume review rejected")

    @task(2)
    def scenario_10_resume_unknown_review(self) -> None:
        self._post_expected(
            f"/review/{uuid.uuid4()}/resume",
            {"approved": True, "notes": "Unknown thread smoke test."},
            "10 resume unknown review",
            expected_status=404,
        )

    @task(2)
    def scenario_11_resume_empty_payload_validation(self) -> None:
        thread_id = self._next_pending_review_id() or str(uuid.uuid4())
        self._post_expected(f"/review/{thread_id}/resume", {}, "11 resume empty payload validation", expected_status={400, 404})

    @task(10)
    def scenario_12_webhook_standard_missing_order(self) -> None:
        self._post_webhook("12 webhook standard missing order", "Order never arrived", "My order #{order_id} never arrived. I am upset and want a refund.")

    @task(8)
    def scenario_13_webhook_direct_ticket_payload(self) -> None:
        order_id = _unique_order_id()
        payload = {
            "id": _unique_ticket_id(),
            "subject": "Direct ticket payload",
            "description": f"My order #{order_id} is missing and I need help.",
            "requester": {"email": _email()},
        }
        self._post_expected("/webhook/zendesk/complaint", payload, "13 webhook direct ticket payload", expected_status=200)

    @task(7)
    def scenario_14_webhook_comment_body(self) -> None:
        order_id = _unique_order_id()
        payload = {
            "ticket": {
                "id": _unique_ticket_id(),
                "subject": "Comment body complaint",
                "comment": {"body": f"My order #{order_id} arrived with missing parts and I need a replacement."},
                "requester": {"email": _email()},
            }
        }
        self._post_expected("/webhook/zendesk/complaint", payload, "14 webhook comment body", expected_status=200)

    @task(7)
    def scenario_15_webhook_via_source_email(self) -> None:
        self._post_webhook_with_via("15 webhook via source email", "Damaged delivery", "My order #{order_id} arrived damaged and I need this fixed.")

    @task(5)
    def scenario_16_webhook_missing_ticket_id(self) -> None:
        order_id = _unique_order_id()
        payload = {
            "ticket": {
                "subject": "No ticket id",
                "description": f"My order #{order_id} has not arrived and I want an update.",
                "requester": {"email": _email()},
            }
        }
        self._post_expected("/webhook/zendesk/complaint", payload, "16 webhook missing ticket id", expected_status=200)

    @task(3)
    def scenario_17_webhook_missing_description_validation(self) -> None:
        payload = {"ticket": {"id": _unique_ticket_id(), "subject": "Missing description", "requester": {"email": _email()}}}
        self._post_expected("/webhook/zendesk/complaint", payload, "17 webhook missing description validation", expected_status=400)

    @task(3)
    def scenario_18_webhook_missing_email_validation(self) -> None:
        payload = {"ticket": {"id": _unique_ticket_id(), "subject": "Missing email", "description": "This payload intentionally omits requester email."}}
        self._post_expected("/webhook/zendesk/complaint", payload, "18 webhook missing email validation", expected_status=400)

    @task(3)
    def scenario_19_webhook_empty_payload_validation(self) -> None:
        self._post_expected("/webhook/zendesk/complaint", {}, "19 webhook empty payload validation", expected_status=400)

    @task(5)
    def scenario_20_webhook_late_delivery(self) -> None:
        self._post_webhook("20 webhook late delivery", "Late delivery", "My order #{order_id} is two weeks late and nobody has explained what happened.")

    @task(5)
    def scenario_21_webhook_damaged_product(self) -> None:
        self._post_webhook("21 webhook damaged product", "Damaged product", "My order #{order_id} arrived cracked and unusable. I want a replacement.")

    @task(5)
    def scenario_22_webhook_wrong_item(self) -> None:
        self._post_webhook("22 webhook wrong item", "Wrong item", "I ordered #{order_id} but received a completely different item.")

    @task(5)
    def scenario_23_webhook_billing_dispute(self) -> None:
        self._post_webhook("23 webhook billing dispute", "Billing dispute", "I was charged twice for order #{order_id} and need the duplicate charge refunded.")

    @task(4)
    def scenario_24_webhook_repeat_contact(self) -> None:
        self._post_webhook("24 webhook repeat contact", "Third contact", "This is my third message about order #{order_id}. I still have no refund or useful answer.")

    @task(4)
    def scenario_25_webhook_angry_customer(self) -> None:
        self._post_webhook("25 webhook angry customer", "Very upset customer", "I am extremely upset that order #{order_id} failed again. I want this escalated now.")

    @task(4)
    def scenario_26_webhook_replacement_request(self) -> None:
        self._post_webhook("26 webhook replacement request", "Replacement request", "Order #{order_id} arrived defective. Please send a replacement immediately.")

    @task(4)
    def scenario_27_webhook_cancellation_request(self) -> None:
        self._post_webhook("27 webhook cancellation request", "Cancel order", "Order #{order_id} has not shipped after ten days. Cancel it and refund me.")

    @task(4)
    def scenario_28_webhook_delivery_address_issue(self) -> None:
        self._post_webhook("28 webhook delivery address issue", "Delivery address issue", "Order #{order_id} was sent to the wrong address even though my confirmation is correct.")

    @task(4)
    def scenario_29_webhook_missing_parts(self) -> None:
        self._post_webhook("29 webhook missing parts", "Missing parts", "Order #{order_id} arrived without the mounting kit, so I cannot use it.")

    @task(4)
    def scenario_30_webhook_quality_complaint(self) -> None:
        self._post_webhook("30 webhook quality complaint", "Poor quality", "Order #{order_id} broke after one day and the quality is unacceptable.")

    @task(2)
    def scenario_31_test_standard_complaint_workflow(self) -> None:
        self._post_test_complaint("31 test standard complaint", "My order #{order_id} never arrived. I contacted support yesterday and still need a refund or replacement.")

    @task(2)
    def scenario_32_test_damaged_product_workflow(self) -> None:
        self._post_test_complaint("32 test damaged product", "My order #{order_id} arrived damaged. The product is unusable and I need a replacement.")

    @task(1)
    def scenario_33_test_high_value_refund_escalation(self) -> None:
        self._post_test_complaint("33 test high-value refund escalation", "My order #{order_id} was a $950 espresso machine that arrived badly damaged. I contacted support twice and want a full refund immediately.")

    @task(2)
    def scenario_34_test_non_complaint_workflow(self) -> None:
        self._post_workflow("/test/complaint", {"email": _email(), "complaint": "Thanks for the update. No problem from my side."}, "34 test non-complaint")

    @task(3)
    def scenario_35_test_missing_complaint_validation(self) -> None:
        self._post_expected("/test/complaint", {"email": _email()}, "35 test missing complaint validation", expected_status=400)

    @task(3)
    def scenario_36_test_empty_complaint_validation(self) -> None:
        self._post_expected("/test/complaint", {"email": _email(), "complaint": ""}, "36 test empty complaint validation", expected_status=400)

    @task(1)
    def scenario_37_test_late_delivery_workflow(self) -> None:
        self._post_test_complaint("37 test late delivery", "Order #{order_id} is late by two weeks and I want a clear answer today.")

    @task(1)
    def scenario_38_test_wrong_item_workflow(self) -> None:
        self._post_test_complaint("38 test wrong item", "I received the wrong item for order #{order_id} and need the correct item shipped.")

    @task(1)
    def scenario_39_test_billing_refund_workflow(self) -> None:
        self._post_test_complaint("39 test billing refund", "I was charged twice for order #{order_id}. Please refund the duplicate charge.")

    @task(1)
    def scenario_40_test_replacement_workflow(self) -> None:
        self._post_test_complaint("40 test replacement", "Order #{order_id} arrived defective and I need a replacement, not store credit.")

    @task(1)
    def scenario_41_test_repeat_complaint_workflow(self) -> None:
        self._post_test_complaint("41 test repeat complaint", "This is my fourth message about order #{order_id}. I still do not have a refund.")

    @task(1)
    def scenario_42_test_urgent_sentiment_workflow(self) -> None:
        self._post_test_complaint("42 test urgent sentiment", "I urgently need order #{order_id} resolved today because this delay is causing real problems.")

    @task(1)
    def scenario_43_test_default_email_workflow(self) -> None:
        order_id = _unique_order_id()
        self._post_workflow("/test/complaint", {"complaint": f"My order #{order_id} never arrived and I need help."}, "43 test default email")

    @task(1)
    def scenario_44_test_excluded_product_language(self) -> None:
        self._post_test_complaint("44 test excluded product language", "Order #{order_id} was a final sale item but arrived damaged. I still need help.")

    @task(1)
    def scenario_45_test_low_confidence_language(self) -> None:
        self._post_test_complaint("45 test low confidence language", "Something is wrong with order #{order_id}, but I am not sure whether it shipped or was billed incorrectly.")

    @task(1)
    def scenario_46_test_apology_only_request(self) -> None:
        self._post_test_complaint("46 test apology-only request", "Order #{order_id} was late. I mainly want an explanation and apology from support.")

    @task(1)
    def scenario_47_test_credit_request(self) -> None:
        self._post_test_complaint("47 test credit request", "Order #{order_id} arrived late. I would accept store credit for the inconvenience.")

    @task(1)
    def scenario_48_test_shipping_update_request(self) -> None:
        self._post_test_complaint("48 test shipping update request", "Order #{order_id} tracking has not moved for five days and support has not replied.")

    @task(1)
    def scenario_49_test_damaged_high_sentiment(self) -> None:
        self._post_test_complaint("49 test damaged high sentiment", "I am furious that order #{order_id} arrived broken after I paid for expedited delivery.")

    @task(1)
    def scenario_50_test_bulk_order_complaint(self) -> None:
        self._post_test_complaint("50 test bulk order complaint", "Several items in bulk order #{order_id} are missing and my business needs a fast resolution.")

    @task(3)
    def scenario_51_health_check_burst_read(self) -> None:
        self._get_expected("/health", "51 health check burst read", expected_status=200, json_field=("status", "healthy"))

    @task(2)
    def scenario_52_review_list_after_ingestion(self) -> None:
        with self.client.get("/review", name="52 review list after ingestion", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Expected 200, got {response.status_code}")
                return
            _remember_review_list(response.json())

    @task(1)
    def scenario_53_unknown_review_with_short_id(self) -> None:
        self._get_expected("/review/not-a-thread", "53 unknown review with short id", expected_status=404)

    @task(1)
    def scenario_54_resume_unknown_with_resolution(self) -> None:
        self._post_expected(
            f"/review/{uuid.uuid4()}/resume",
            {
                "approved": True,
                "notes": "Unknown review with resolution payload.",
                "resolution": {"resolution_type": "apology", "confidence": 0.9},
            },
            "54 resume unknown with resolution",
            expected_status=404,
        )

    @task(4)
    def scenario_55_webhook_subscription_issue(self) -> None:
        self._post_webhook("55 webhook subscription issue", "Subscription issue", "My subscription order #{order_id} renewed incorrectly and I need support.")

    @task(4)
    def scenario_56_webhook_premium_shipping_refund(self) -> None:
        self._post_webhook("56 webhook premium shipping refund", "Premium shipping refund", "I paid for premium shipping on order #{order_id}, but it arrived late. Refund the shipping fee.")

    @task(4)
    def scenario_57_webhook_return_label_missing(self) -> None:
        self._post_webhook("57 webhook return label missing", "Return label missing", "Support promised a return label for order #{order_id}, but I never received it.")

    @task(4)
    def scenario_58_webhook_warranty_claim(self) -> None:
        self._post_webhook("58 webhook warranty claim", "Warranty claim", "Order #{order_id} failed under warranty and I need a repair or replacement.")

    @task(4)
    def scenario_59_webhook_gift_order_problem(self) -> None:
        self._post_webhook("59 webhook gift order problem", "Gift order problem", "Order #{order_id} was a gift and arrived too late to be useful. I want a refund.")

    @task(4)
    def scenario_60_webhook_perishable_damage(self) -> None:
        self._post_webhook("60 webhook perishable damage", "Perishable item damaged", "Order #{order_id} contained perishable items that arrived spoiled and unusable.")

    @task(4)
    def scenario_61_webhook_partial_delivery(self) -> None:
        self._post_webhook("61 webhook partial delivery", "Partial delivery", "Only half of order #{order_id} arrived, but I was charged for everything.")

    @task(4)
    def scenario_62_webhook_tracking_delivered_not_received(self) -> None:
        self._post_webhook("62 webhook tracking delivered not received", "Delivered not received", "Tracking says order #{order_id} was delivered, but nothing arrived at my address.")

    @task(4)
    def scenario_63_webhook_account_credit_missing(self) -> None:
        self._post_webhook("63 webhook account credit missing", "Missing account credit", "I was promised credit for order #{order_id}, but it never appeared on my account.")

    @task(4)
    def scenario_64_webhook_refund_delay(self) -> None:
        self._post_webhook("64 webhook refund delay", "Refund delay", "My refund for order #{order_id} was approved weeks ago, but I still have not received it.")

    @task(4)
    def scenario_65_webhook_exchange_request(self) -> None:
        self._post_webhook("65 webhook exchange request", "Exchange request", "Order #{order_id} is the wrong size and I need an exchange, not another delay.")

    @task(4)
    def scenario_66_webhook_vip_customer_escalation(self) -> None:
        self._post_webhook("66 webhook VIP customer escalation", "VIP escalation", "I am a long-time customer and order #{order_id} failed badly. Please escalate this.")

    @task(4)
    def scenario_67_webhook_social_media_risk(self) -> None:
        self._post_webhook("67 webhook social media risk", "Public complaint risk", "If order #{order_id} is not fixed today, I will share this experience publicly.")

    @task(4)
    def scenario_68_webhook_accessibility_issue(self) -> None:
        self._post_webhook("68 webhook accessibility issue", "Accessibility issue", "Order #{order_id} instructions were inaccessible and I need a replacement format.")

    @task(4)
    def scenario_69_webhook_installation_failure(self) -> None:
        self._post_webhook("69 webhook installation failure", "Installation failure", "Order #{order_id} cannot be installed because required hardware is missing.")

    @task(4)
    def scenario_70_webhook_multiple_orders_one_ticket(self) -> None:
        first_order = _unique_order_id()
        second_order = _unique_order_id()
        payload = {
            "ticket": {
                "id": _unique_ticket_id(),
                "subject": "Multiple order complaint",
                "description": f"Orders #{first_order} and #{second_order} both arrived damaged, and I need this handled together.",
                "requester": {"email": _email()},
            }
        }
        self._post_expected("/webhook/zendesk/complaint", payload, "70 webhook multiple orders one ticket", expected_status=200)

    @task(4)
    def scenario_71_webhook_comment_body_billing(self) -> None:
        order_id = _unique_order_id()
        payload = {
            "ticket": {
                "id": _unique_ticket_id(),
                "subject": "Comment billing dispute",
                "comment": {"body": f"I was charged the wrong amount for order #{order_id} and need a correction."},
                "requester": {"email": _email()},
            }
        }
        self._post_expected("/webhook/zendesk/complaint", payload, "71 webhook comment body billing", expected_status=200)

    @task(4)
    def scenario_72_webhook_via_email_refund_delay(self) -> None:
        self._post_webhook_with_via("72 webhook via email refund delay", "Refund delay via email", "Refund for order #{order_id} has not arrived after two weeks.")

    @task(4)
    def scenario_73_webhook_direct_payload_wrong_address(self) -> None:
        order_id = _unique_order_id()
        payload = {
            "id": _unique_ticket_id(),
            "subject": "Direct wrong address",
            "description": f"Order #{order_id} went to an old address even though my profile is updated.",
            "requester": {"email": _email()},
        }
        self._post_expected("/webhook/zendesk/complaint", payload, "73 webhook direct payload wrong address", expected_status=200)

    @task(4)
    def scenario_74_webhook_direct_payload_return_issue(self) -> None:
        order_id = _unique_order_id()
        payload = {
            "id": _unique_ticket_id(),
            "subject": "Direct return issue",
            "description": f"I returned order #{order_id}, but the return is still not reflected on my account.",
            "requester": {"email": _email()},
        }
        self._post_expected("/webhook/zendesk/complaint", payload, "74 webhook direct payload return issue", expected_status=200)

    @task(2)
    def scenario_75_webhook_invalid_blank_description(self) -> None:
        payload = {"ticket": {"id": _unique_ticket_id(), "subject": "Blank description", "description": "", "requester": {"email": _email()}}}
        self._post_expected("/webhook/zendesk/complaint", payload, "75 webhook invalid blank description", expected_status=400)

    @task(2)
    def scenario_76_webhook_invalid_empty_comment_body(self) -> None:
        payload = {"ticket": {"id": _unique_ticket_id(), "subject": "Blank comment", "comment": {"body": ""}, "requester": {"email": _email()}}}
        self._post_expected("/webhook/zendesk/complaint", payload, "76 webhook invalid empty comment body", expected_status=400)

    @task(2)
    def scenario_77_webhook_invalid_requester_empty_object(self) -> None:
        payload = {"ticket": {"id": _unique_ticket_id(), "subject": "Empty requester", "description": "Order issue needs help.", "requester": {}}}
        self._post_expected("/webhook/zendesk/complaint", payload, "77 webhook invalid requester empty object", expected_status=400)

    @task(2)
    def scenario_78_webhook_invalid_via_empty_source(self) -> None:
        payload = {"ticket": {"id": _unique_ticket_id(), "subject": "Empty via", "description": "Order issue needs help.", "via": {"source": {}}}}
        self._post_expected("/webhook/zendesk/complaint", payload, "78 webhook invalid via empty source", expected_status=400)

    @task(2)
    def scenario_79_webhook_invalid_nested_ticket_empty(self) -> None:
        self._post_expected("/webhook/zendesk/complaint", {"ticket": {}}, "79 webhook invalid nested ticket empty", expected_status=400)

    @task(2)
    def scenario_80_webhook_invalid_subject_only(self) -> None:
        self._post_expected("/webhook/zendesk/complaint", {"subject": "Subject only"}, "80 webhook invalid subject only", expected_status=400)

    @task(1)
    def scenario_81_test_subscription_issue_workflow(self) -> None:
        self._post_test_complaint("81 test subscription issue", "My subscription order #{order_id} renewed incorrectly and I need the charge fixed.")

    @task(1)
    def scenario_82_test_premium_shipping_refund_workflow(self) -> None:
        self._post_test_complaint("82 test premium shipping refund", "I paid for premium shipping on order #{order_id}, but it arrived late. Refund that fee.")

    @task(1)
    def scenario_83_test_return_label_missing_workflow(self) -> None:
        self._post_test_complaint("83 test return label missing", "I still have not received the return label for order #{order_id} after support promised it.")

    @task(1)
    def scenario_84_test_warranty_claim_workflow(self) -> None:
        self._post_test_complaint("84 test warranty claim", "Order #{order_id} failed while under warranty and I need a replacement.")

    @task(1)
    def scenario_85_test_gift_order_problem_workflow(self) -> None:
        self._post_test_complaint("85 test gift order problem", "Order #{order_id} was a gift that arrived too late, and I want a refund.")

    @task(1)
    def scenario_86_test_perishable_damage_workflow(self) -> None:
        self._post_test_complaint("86 test perishable damage", "Order #{order_id} arrived spoiled and unusable, so I need a full refund.")

    @task(1)
    def scenario_87_test_partial_delivery_workflow(self) -> None:
        self._post_test_complaint("87 test partial delivery", "Only part of order #{order_id} arrived, but I was billed for the full order.")

    @task(1)
    def scenario_88_test_delivered_not_received_workflow(self) -> None:
        self._post_test_complaint("88 test delivered not received", "Tracking says order #{order_id} was delivered, but I never received it.")

    @task(1)
    def scenario_89_test_account_credit_missing_workflow(self) -> None:
        self._post_test_complaint("89 test account credit missing", "The credit promised for order #{order_id} has not appeared on my account.")

    @task(1)
    def scenario_90_test_refund_delay_workflow(self) -> None:
        self._post_test_complaint("90 test refund delay", "Refund for order #{order_id} was approved weeks ago, but the money has not arrived.")

    @task(1)
    def scenario_91_test_exchange_request_workflow(self) -> None:
        self._post_test_complaint("91 test exchange request", "Order #{order_id} is the wrong size and I need an exchange as soon as possible.")

    @task(1)
    def scenario_92_test_vip_customer_escalation_workflow(self) -> None:
        self._post_test_complaint("92 test VIP customer escalation", "I am a long-time customer and order #{order_id} failed badly. Escalate this please.")

    @task(1)
    def scenario_93_test_social_media_risk_workflow(self) -> None:
        self._post_test_complaint("93 test social media risk", "If order #{order_id} is not fixed today, I will share this publicly.")

    @task(1)
    def scenario_94_test_accessibility_issue_workflow(self) -> None:
        self._post_test_complaint("94 test accessibility issue", "The instructions for order #{order_id} were inaccessible and I need support.")

    @task(1)
    def scenario_95_test_installation_failure_workflow(self) -> None:
        self._post_test_complaint("95 test installation failure", "Order #{order_id} cannot be installed because the required hardware is missing.")

    @task(1)
    def scenario_96_test_multiple_orders_workflow(self) -> None:
        first_order = _unique_order_id()
        second_order = _unique_order_id()
        self._post_workflow(
            "/test/complaint",
            {"email": _email(), "complaint": f"Orders #{first_order} and #{second_order} both have issues, and I need one support plan."},
            "96 test multiple orders",
        )

    @task(1)
    def scenario_97_test_high_value_lost_package_workflow(self) -> None:
        self._post_test_complaint("97 test high-value lost package", "My $1200 order #{order_id} is lost, and I need a full refund immediately.")

    @task(1)
    def scenario_98_test_low_value_credit_workflow(self) -> None:
        self._post_test_complaint("98 test low-value credit", "A small accessory in order #{order_id} arrived late. A modest credit would be fine.")

    @task(1)
    def scenario_99_test_duplicate_case_language_workflow(self) -> None:
        self._post_test_complaint("99 test duplicate case language", "I already opened a case for order #{order_id}, but no one has replied.")

    @task(1)
    def scenario_100_test_formal_complaint_workflow(self) -> None:
        self._post_test_complaint("100 test formal complaint", "Please treat this as a formal complaint: order #{order_id} failed, support did not respond, and I need resolution.")
    def _get_expected(
        self,
        path: str,
        name: str,
        *,
        expected_status: int | set[int],
        json_field: tuple[str, Any] | None = None,
    ) -> None:
        statuses = expected_status if isinstance(expected_status, set) else {expected_status}
        with self.client.get(path, name=name, catch_response=True) as response:
            if response.status_code not in statuses:
                response.failure(f"Expected {sorted(statuses)}, got {response.status_code}")
                return
            if json_field and response.status_code < 400:
                key, expected_value = json_field
                body = response.json()
                if body.get(key) != expected_value:
                    response.failure(f"Unexpected {key}: {body}")

    def _post_webhook(self, name: str, subject: str, description_template: str) -> None:
        order_id = _unique_order_id()
        payload = {
            "ticket": {
                "id": _unique_ticket_id(),
                "subject": subject,
                "description": description_template.format(order_id=order_id),
                "requester": {"email": _email()},
            }
        }
        self._post_expected("/webhook/zendesk/complaint", payload, name, expected_status=200)

    def _post_webhook_with_via(self, name: str, subject: str, description_template: str) -> None:
        order_id = _unique_order_id()
        payload = {
            "ticket": {
                "id": _unique_ticket_id(),
                "subject": subject,
                "description": description_template.format(order_id=order_id),
                "via": {"source": {"from": {"address": _email()}}},
            }
        }
        self._post_expected("/webhook/zendesk/complaint", payload, name, expected_status=200)

    def _post_test_complaint(self, name: str, complaint_template: str) -> None:
        order_id = _unique_order_id()
        payload = {
            "email": _email(),
            "complaint": complaint_template.format(order_id=order_id),
        }
        self._post_workflow("/test/complaint", payload, name)

    def _post_review_resume(self, thread_id: str, payload: dict[str, Any], name: str) -> None:
        self._post_expected(f"/review/{thread_id}/resume", payload, name, expected_status={200, 404})

    def _post_expected(
        self,
        path: str,
        payload: dict[str, Any],
        name: str,
        *,
        expected_status: int | set[int],
    ) -> None:
        statuses = expected_status if isinstance(expected_status, set) else {expected_status}
        with self.client.post(path, json=payload, name=name, catch_response=True) as response:
            if response.status_code not in statuses:
                response.failure(f"Expected {sorted(statuses)}, got {response.status_code}")
                return
            if response.status_code < 400:
                _remember_pending_review(response.json())

    def _post_workflow(self, path: str, payload: dict[str, Any], name: str) -> None:
        with self.client.post(path, json=payload, name=name, catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Expected 200, got {response.status_code}")
                return
            body = response.json()
            if body.get("status") not in {"completed", "pending_review"}:
                response.failure(f"Unexpected workflow status: {body}")
                return
            _remember_pending_review(body)

    def _next_pending_review_id(self) -> str | None:
        if not PENDING_REVIEW_IDS:
            return None
        return random.choice(tuple(PENDING_REVIEW_IDS))

    def _pop_pending_review_id(self) -> str | None:
        if not PENDING_REVIEW_IDS:
            return None
        return PENDING_REVIEW_IDS.popleft()

