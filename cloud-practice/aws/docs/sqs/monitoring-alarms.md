# SQS — CloudWatch Metrics & Alarms (plain-English guide)

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).

Think of an SQS queue like a **physical mailbox**: messages pile up waiting to be picked up by a worker (consumer). CloudWatch metrics tell you what's happening inside that mailbox, and alarms are the smoke detector that yells when something looks wrong.

---

## 1. The core SQS metrics

### `ApproximateNumberOfMessagesVisible`
- **What it is:** How many messages are sitting in the queue, waiting to be picked up.
- **Plain English:** "How big is the backlog right now?" If this keeps climbing, messages are arriving faster than your workers can process them.
- **Alarm idea:** Fire if this goes above e.g. 1000 — consumers can't keep up.

### `ApproximateNumberOfMessagesNotVisible`
- **What it is:** Messages already picked up by a worker but not yet deleted (in flight, hidden during the visibility timeout).
- **Plain English:** "How many messages are currently being worked on but not finished yet?"
- **Alarm idea:** Staying high for a long time suggests workers are stuck or crashing before finishing (message keeps reappearing).

### `ApproximateNumberOfMessagesDelayed`
- **What it is:** Messages scheduled to appear later (delay queues) — they exist but aren't visible yet.
- **Plain English:** "Messages sitting in a waiting room before they're even allowed to enter the queue."
- **Alarm idea:** Rarely alarmed directly; a spike when you expect zero can mean a config bug.

### `ApproximateAgeOfOldestMessage`
- **What it is:** How long (seconds) the oldest message has been sitting unprocessed.
- **Plain English:** "What's the longest anything has been waiting?" Often the **single most useful** metric to alarm on.
- **Alarm idea:** Fire if a message has waited > 300–600s — catches a stuck pipeline even when the queue *count* looks small.

### `NumberOfMessagesSent`
- **What it is:** Count of messages added to the queue.
- **Plain English:** "How much mail is coming in?"
- **Alarm idea:** Detect traffic spikes/drops (e.g., a producer went down and sent 0 messages).

### `NumberOfMessagesReceived`
- **What it is:** Count of messages a consumer polled, including ones that later time out and get re-delivered.
- **Plain English:** "How much mail is being read/picked up?"

### `NumberOfMessagesDeleted`
- **What it is:** Count of messages successfully deleted after processing (i.e., successfully finished).
- **Plain English:** "How much work actually got completed?"
- **Alarm idea:** If `Sent` stays much greater than `Deleted` over time, the backlog is growing.

### `NumberOfEmptyReceives`
- **What it is:** Number of times a consumer polled and found nothing.
- **Plain English:** "How often did the worker check the mailbox and find it empty?"
- **Alarm idea:** High values can mean wasted API calls/cost — polling too aggressively for a low-traffic queue.

### `SentMessageSize`
- **What it is:** Size (bytes) of messages sent.
- **Plain English:** "How big is each letter?"
- **Alarm idea:** Rarely alarmed, but useful to catch abnormal payloads.

---

## 2. What each alarm setting actually means

| Parameter | Plain-English explanation |
|---|---|
| **Metric** | Which of the numbers above you're watching (e.g., queue depth). |
| **Statistic** | How to summarize the raw data points in each period: `Average`, `Sum`, `Maximum`, `Minimum`, `SampleCount`. Do you want the *typical* value, the *total*, or the *worst-case peak*? For queue depth, people usually use `Maximum` or `Average`. |
| **Period** | The time chunk the statistic is calculated over — e.g., 60s, 300s. Smaller = more sensitive/noisy; larger = smoother but slower to react. |
| **Evaluation Periods** | How many of those time chunks in a row to look at before deciding there's a real problem (e.g., "check the last 5 periods"). |
| **Datapoints to Alarm** | Out of those evaluation periods, how many must actually breach the threshold to trigger (e.g., "3 out of 5") — avoids false alarms from one noisy blip. |
| **Threshold** | The actual number that counts as "too much" or "too little" (e.g., 1000 messages). |
| **Comparison Operator** | Whether you alarm when the value is `GreaterThanThreshold`, `LessThanThreshold`, etc. |
| **Missing Data Treatment** | What to do if CloudWatch has no data point for a period (e.g., zero activity). Options: `missing` (ignore), `notBreaching` (treat as OK), `breaching` (treat as bad), `ignore` (keep last alarm state). |
| **Alarm State** | `OK` (fine), `ALARM` (threshold breached), `INSUFFICIENT_DATA` (not enough data yet to judge). |
| **Actions** | What happens when the alarm fires — typically an SNS notification (email, Slack, PagerDuty), or an Auto Scaling action. |

---

## 3. Period vs. Evaluation Periods — the part people mix up

These are two different knobs and it's easy to conflate them:

- **Period** = the time bucket CloudWatch groups raw data points into (e.g. 15 minutes). It doesn't decide *when* to alarm — it decides how much data gets squashed into one number.
- **Evaluation Periods** = how many of those buckets in a row get checked before the alarm can fire. Default is 1.

**Concrete example:** alarm on `ApproximateNumberOfMessagesVisible` > 1000, Period = 15 minutes, Evaluation Periods = 1 (default).

Every 15 minutes, CloudWatch does this:
1. Take all the raw queue-depth readings from the last 15 minutes.
2. Collapse them into one number using the **Statistic** (e.g. `Average` or `Maximum`).
3. Is that number > 1000? If yes → `ALARM`. If Evaluation Periods were 2 instead of 1, it would need **two consecutive** 15-minute windows over 1000 (30 minutes of sustained backlog) before firing — useful for ignoring one-off blips.

**Gotcha:** if the Statistic is `Average`, a queue that spikes to 5000 messages for 2 minutes and drains back to 50 can average out to well under 1000 across the full 15-minute window and **never trigger** — even though a real spike happened. For queue-depth alarms, `Maximum` is usually the safer statistic than `Average`, since it catches the peak instead of smoothing it away.

---

## 4. Worked example

Goal: know if an order-processing pipeline is falling behind.

- **Metric:** `ApproximateAgeOfOldestMessage`
- **Statistic:** Maximum
- **Period:** 300s (5 min)
- **Evaluation Periods:** 3
- **Datapoints to Alarm:** 3 out of 3
- **Threshold:** > 600s (10 min)
- **Comparison:** GreaterThanThreshold

**In plain English:** "If, for 3 straight 5-minute windows, the oldest message in the queue has been waiting more than 10 minutes, something is wrong — alert me." This is a better signal than watching queue *size* alone: a small queue with one severely stuck message is often worse than a large queue that's actively draining.

---

## 5. Dimensions — which queue is this actually measuring?

Every SQS metric is published per-queue via the `QueueName` dimension. CloudWatch doesn't aggregate across queues automatically — an alarm is always scoped to one specific queue's ARN/name. If you have a main queue and a DLQ, they are **two separate sets of metrics**, even though they're related (see below).

---

## 6. Alarm actions — what happens on each state change

An alarm isn't just ON/OFF — it has three states, and you can wire a different action to each transition:

- **ALARM actions** — fires when state goes to `ALARM`. Typically an SNS topic → email/Slack/PagerDuty, or an Auto Scaling policy (e.g., scale up consumer workers).
- **OK actions** — fires when state goes back to `OK`. Useful for an "all clear" notification, or to scale a fleet back down.
- **INSUFFICIENT_DATA actions** — fires when there isn't enough data to evaluate (e.g., queue had zero traffic so no data points existed). Often left empty, but useful if "no data" itself is suspicious (e.g., a producer that should always be sending something).

**Plain English:** think of these as three different doorbells — one rings when trouble starts, one rings when it's resolved, and one rings if the monitor itself goes quiet.

---

## 7. Dead Letter Queue (DLQ) metrics & redrive alarms

A DLQ catches messages that failed processing too many times (exceeded `maxReceiveCount`). It's a **separate queue** with its own full set of the same metrics above. The two you actually care about:

### `ApproximateNumberOfMessagesVisible` (on the DLQ)
- **Plain English:** "How many messages have given up and landed in the reject pile?"
- **Alarm idea:** Alarm on **any value > 0** (threshold = 0, `GreaterThanThreshold`). Unlike the main queue, a healthy DLQ should usually be *empty* — even one message often means a bug is silently dropping data, so don't wait for a big number before alerting.

### `NumberOfMessagesSent` (on the DLQ)
- **Plain English:** "How many messages just got kicked out of the main queue and dumped here?"
- **Alarm idea:** Useful to catch a burst of failures in real time, rather than only noticing the backlog after it's built up.

**Redrive:** once you fix the underlying bug, use the SQS **redrive** feature (console "Start DLQ redrive" or `StartMessageMoveTask` API) to replay DLQ messages back into the source queue. There's no dedicated CloudWatch metric for redrive progress — monitor it via the DLQ's `ApproximateNumberOfMessagesVisible` dropping back toward 0.

---

## 8. Recommended alarm recipes (starting points, tune to your traffic)

| Goal | Metric | Statistic | Period | Threshold | Why |
|---|---|---|---|---|---|
| Consumers falling behind | `ApproximateAgeOfOldestMessage` | Maximum | 5 min | > 300–900s | Catches a stuck pipeline even with low message counts. |
| Backlog growing | `ApproximateNumberOfMessagesVisible` | Maximum | 5–15 min | depends on normal volume | Use `Maximum`, not `Average`, so a spike isn't smoothed away (see §3). |
| Producer stopped sending | `NumberOfMessagesSent` | Sum | 15 min | < expected minimum | `LessThanThreshold` — silence can be as bad as a spike. |
| Messages failing repeatedly | DLQ `ApproximateNumberOfMessagesVisible` | Maximum | 5 min | > 0 | DLQ should normally be empty; alarm on the first message, not a big pile. |
| Workers stuck mid-processing | `ApproximateNumberOfMessagesNotVisible` | Maximum | 5–15 min | sustained high value | Combine with a check on visibility timeout duration. |

---

## 9. CLI example

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name "sqs-orders-oldest-message-age" \
  --namespace "AWS/SQS" \
  --metric-name "ApproximateAgeOfOldestMessage" \
  --dimensions Name=QueueName,Value=orders-queue \
  --statistic Maximum \
  --period 300 \
  --evaluation-periods 3 \
  --datapoints-to-alarm 3 \
  --threshold 600 \
  --comparison-operator GreaterThanThreshold \
  --treat-missing-data notBreaching \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:ops-alerts
```

This is the CLI version of the worked example in §4: "if the oldest message has waited over 10 minutes for 3 straight 5-minute checks, notify the `ops-alerts` SNS topic."

---

## 10. Terraform example

```hcl
resource "aws_sqs_queue" "orders" {
  name = "orders-queue"
}

resource "aws_sqs_queue" "orders_dlq" {
  name = "orders-queue-dlq"
}

resource "aws_sns_topic" "ops_alerts" {
  name = "ops-alerts"
}

# Backlog age alarm on the main queue
resource "aws_cloudwatch_metric_alarm" "orders_oldest_message" {
  alarm_name          = "sqs-orders-oldest-message-age"
  namespace           = "AWS/SQS"
  metric_name         = "ApproximateAgeOfOldestMessage"
  dimensions          = { QueueName = aws_sqs_queue.orders.name }
  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 3
  datapoints_to_alarm = 3
  threshold           = 600
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.ops_alerts.arn]
  ok_actions          = [aws_sns_topic.ops_alerts.arn]
}

# Any message landing in the DLQ is worth an immediate alert
resource "aws_cloudwatch_metric_alarm" "orders_dlq_not_empty" {
  alarm_name          = "sqs-orders-dlq-has-messages"
  namespace           = "AWS/SQS"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  dimensions          = { QueueName = aws_sqs_queue.orders_dlq.name }
  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 1
  datapoints_to_alarm = 1
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.ops_alerts.arn]
}
```

Full reusable module (if you want one): [`../../terraform/sqs/`](../../terraform/sqs/README.md) — not created yet in this repo.
