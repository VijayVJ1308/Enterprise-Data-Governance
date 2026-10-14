"""
Phase 19: Apache Kafka Streaming Ingestion & Real-Time Alerting Tests.

Tests:
1. Configuration & Managed Topics
2. StreamMessage JSON Serialization
3. Producer Event Publishing & Partitioning
4. Consumer Polling & Manual Offset Commits
5. Micro-batch Medallion Bronze Lakehouse Landing
6. Real-time Wire-level Quality Alert Filter
7. Alert Channel Dispatch Formatters (Slack, PagerDuty, Email)
8. Dead Letter Queue (DLQ) Routing
"""

import os
import shutil
import tempfile
import unittest

from kafka.config import KafkaConfig
from kafka.message import StreamMessage
from kafka.broker import StreamingBroker
from kafka.producer import StreamingProducer
from kafka.consumer import StreamingConsumer
from kafka.alerting import StreamingAlertEngine, QualityAlert


class TestPhase19KafkaStreaming(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        StreamingBroker.reset_instance()
        self.broker = StreamingBroker()
        self.config = KafkaConfig()
        self.producer = StreamingProducer(config=self.config, broker=self.broker)
        self.alert_engine = StreamingAlertEngine(config=self.config, broker=self.broker)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        StreamingBroker.reset_instance()

    def test_kafka_config_and_managed_topics(self):
        topics = self.config.get_all_managed_topics()
        self.assertEqual(len(topics), 6)
        self.assertIn("enterprise.crm.events", topics)
        self.assertIn("enterprise.erp.transactions", topics)
        self.assertIn("enterprise.ecommerce.orders", topics)
        self.assertIn("enterprise.quality.alerts", topics)
        self.assertIn("enterprise.governance.audit", topics)
        self.assertIn("enterprise.dlq", topics)

    def test_stream_message_serialization(self):
        payload = {"customer_id": "CUST-1001", "email": "alice@corp.com", "balance": 1500.5}
        headers = {"source": "CRM_APP", "region": "US_EAST"}
        msg = StreamMessage(
            topic="enterprise.crm.events",
            value=payload,
            key="CUST-1001",
            headers=headers,
            partition=1,
            offset=42,
        )

        json_str = msg.to_json()
        deserialized = StreamMessage.from_json(json_str)

        self.assertEqual(deserialized.topic, msg.topic)
        self.assertEqual(deserialized.key, "CUST-1001")
        self.assertEqual(deserialized.value["email"], "alice@corp.com")
        self.assertEqual(deserialized.partition, 1)
        self.assertEqual(deserialized.offset, 42)
        self.assertEqual(deserialized.headers["source"], "CRM_APP")

    def test_producer_event_emissions_and_headers(self):
        # CRM Customer Event
        crm_msg = self.producer.emit_crm_customer_event(
            customer_id="CUST-5501",
            action="created",
            customer_data={"first_name": "Diana", "email": "diana@enterprise.org"},
        )
        self.assertEqual(crm_msg.topic, self.config.TOPIC_CRM_EVENTS)
        self.assertEqual(crm_msg.key, "CUST-5501")
        self.assertIn("producer_id", crm_msg.headers)
        self.assertIn("trace_id", crm_msg.headers)
        self.assertEqual(crm_msg.headers["domain"], "CRM")

        # ERP Transaction Event
        erp_msg = self.producer.emit_erp_transaction_event(
            txn_id="TXN-9021",
            amount_usd=12500.75,
            currency="USD",
            txn_data={"gl_account": "1001-CASH"},
        )
        self.assertEqual(erp_msg.topic, self.config.TOPIC_ERP_TRANSACTIONS)
        self.assertEqual(erp_msg.value["amount_usd"], 12500.75)

        # Ecommerce Order Event
        order_msg = self.producer.emit_order_event(
            order_id="ORD-774",
            customer_id="CUST-5501",
            total_amount=320.0,
            status="CONFIRMED",
        )
        self.assertEqual(order_msg.topic, self.config.TOPIC_ECOMMERCE_ORDERS)
        self.assertEqual(order_msg.value["status"], "CONFIRMED")

    def test_consumer_polling_and_offset_commit(self):
        # Publish 4 messages to ERP topic
        for i in range(4):
            self.producer.emit_erp_transaction_event(
                txn_id=f"TXN-{100 + i}",
                amount_usd=100.0 * (i + 1),
                currency="USD",
                txn_data={},
            )

        consumer = StreamingConsumer(
            topics=[self.config.TOPIC_ERP_TRANSACTIONS],
            group_id="finance_pipeline_group",
            config=self.config,
            broker=self.broker,
        )

        # Poll first batch of 2 messages
        batch1 = consumer.poll(max_messages=2, auto_commit=False)
        self.assertEqual(len(batch1), 2)

        # Commit offset
        consumer.commit()

        # Second poll should fetch remaining 2 messages
        batch2 = consumer.poll(max_messages=10, auto_commit=False)
        self.assertEqual(len(batch2), 2)
        consumer.commit()

        # Third poll should be empty
        batch3 = consumer.poll(max_messages=10, auto_commit=False)
        self.assertEqual(len(batch3), 0)

    def test_consumer_micro_batch_bronze_lakehouse_landing(self):
        # Publish 3 CRM customer records
        for i in range(3):
            self.producer.emit_crm_customer_event(
                customer_id=f"CUST-STREAM-{i}",
                action="onboarded",
                customer_data={"email": f"user{i}@test.com", "tier": "GOLD"},
            )

        consumer = StreamingConsumer(
            topics=[self.config.TOPIC_CRM_EVENTS],
            group_id="bronze_landing_group",
            config=self.config,
            broker=self.broker,
        )

        result = consumer.consume_to_bronze(
            dataset_name="crm_customers",
            topic=self.config.TOPIC_CRM_EVENTS,
            bronze_output_dir=self.temp_dir,
            max_records=10,
        )

        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["record_count"], 3)
        self.assertTrue(os.path.exists(result["output_file"]))

        # Verify landed file contains enriched metadata headers
        with open(result["output_file"], "r", encoding="utf-8") as f:
            import json
            records = json.load(f)
            self.assertEqual(len(records), 3)
            first = records[0]
            self.assertIn("_ingestion_id", first)
            self.assertIn("_ingestion_timestamp", first)
            self.assertIn("_record_hash", first)
            self.assertEqual(first["_source_type"], "kafka")
            self.assertEqual(first["_source_identifier"], self.config.TOPIC_CRM_EVENTS)

    def test_real_time_wire_level_quality_alerting(self):
        # 1. Valid ERP Transaction - No alert
        valid_msg = self.producer.emit_erp_transaction_event(
            txn_id="TXN-VALID-1",
            amount_usd=450.0,
            currency="USD",
            txn_data={},
        )
        alerts_valid = self.alert_engine.inspect_and_publish(valid_msg)
        self.assertEqual(len(alerts_valid), 0)

        # 2. Critical Negative Amount Violation
        neg_msg = self.producer.emit_erp_transaction_event(
            txn_id="TXN-ANOMALOUS-2",
            amount_usd=-8500.0,
            currency="USD",
            txn_data={},
        )
        alerts_neg = self.alert_engine.inspect_and_publish(neg_msg)
        self.assertEqual(len(alerts_neg), 1)
        self.assertEqual(alerts_neg[0].rule_code, "STREAM_VAL_NEGATIVE_AMOUNT")
        self.assertEqual(alerts_neg[0].severity, "CRITICAL")
        self.assertEqual(alerts_neg[0].record_id, "TXN-ANOMALOUS-2")

        # 3. Invalid Email Format in CRM Stream
        bad_email_msg = self.producer.emit_crm_customer_event(
            customer_id="CUST-BAD-EMAIL",
            action="profile_update",
            customer_data={"email": "invalid_email_at_nowhere"},
        )
        alerts_email = self.alert_engine.inspect_and_publish(bad_email_msg)
        self.assertEqual(len(alerts_email), 1)
        self.assertEqual(alerts_email[0].rule_code, "STREAM_VAL_INVALID_EMAIL")
        self.assertEqual(alerts_email[0].severity, "HIGH")

        # 4. Verify alerts were published to the quality alerts topic
        alert_count = self.broker.get_topic_message_count(self.config.TOPIC_QUALITY_ALERTS)
        self.assertEqual(alert_count, 2)

    def test_alert_channel_dispatch_formatters(self):
        alert = QualityAlert(
            alert_id="ALT-TEST-99",
            rule_code="STREAM_VAL_NEGATIVE_AMOUNT",
            severity="CRITICAL",
            topic="enterprise.erp.transactions",
            record_id="TXN-1234",
            dimension="validity",
            description="Negative transaction amount detected on wire: -1500 USD",
            payload_snapshot={"txn_id": "TXN-1234", "amount_usd": -1500.0},
        )

        # Slack
        slack_payload = StreamingAlertEngine.format_slack_webhook(alert, channel="#alerts")
        self.assertEqual(slack_payload["channel"], "#alerts")
        self.assertEqual(slack_payload["attachments"][0]["color"], "#ef4444")
        self.assertIn("STREAM_VAL_NEGATIVE_AMOUNT", slack_payload["attachments"][0]["title"])

        # PagerDuty
        pd_payload = StreamingAlertEngine.format_pagerduty_incident(alert, service_key="KEY-ABC")
        self.assertEqual(pd_payload["routing_key"], "KEY-ABC")
        self.assertEqual(pd_payload["payload"]["severity"], "critical")
        self.assertEqual(pd_payload["event_action"], "trigger")

        # Email
        email_payload = StreamingAlertEngine.format_email_alert(alert, recipients=["alerts@corp.com"])
        self.assertIn("alerts@corp.com", email_payload["to"])
        self.assertIn("STREAM_VAL_NEGATIVE_AMOUNT", email_payload["subject"])
        self.assertIn("CRITICAL", email_payload["body"])

    def test_dead_letter_queue_handling(self):
        consumer = StreamingConsumer(
            topics=[self.config.TOPIC_ECOMMERCE_ORDERS],
            group_id="order_processor",
            config=self.config,
            broker=self.broker,
        )

        malformed_record = "{ corrupted_json_stream_payload }"
        error = ValueError("JSONDecodeError: Expecting property name enclosed in double quotes")

        dlq_msg = consumer.route_to_dlq(malformed_record, error)
        self.assertEqual(dlq_msg.topic, self.config.TOPIC_DEAD_LETTER_QUEUE)
        self.assertEqual(dlq_msg.value["error_type"], "ValueError")
        self.assertEqual(dlq_msg.headers["is_dlq"], "true")

        # Verify DLQ topic has the recorded failure
        dlq_count = self.broker.get_topic_message_count(self.config.TOPIC_DEAD_LETTER_QUEUE)
        self.assertGreaterEqual(dlq_count, 1)


if __name__ == "__main__":
    unittest.main()
