"""Live verification script checking all 6 running services over HTTP."""

import sys

import httpx

PORTS = [
    (8000, "api-gateway"),
    (8001, "research-orchestrator"),
    (8002, "ingestion-service"),
    (8003, "retrieval-service"),
    (8004, "agent-runtime"),
    (8005, "evaluation-service"),
]

all_passed = True
custom_trace_id = "trace-live-verify-12345"

with httpx.Client(timeout=5.0) as client:
    for port, expected_name in PORTS:
        base_url = f"http://127.0.0.1:{port}"
        try:
            # 1. Liveness Check
            live_resp = client.get(
                f"{base_url}/health/live",
                headers={"X-Correlation-ID": custom_trace_id},
            )
            live_data = live_resp.json()
            corr_returned = live_resp.headers.get("x-correlation-id")

            # 2. Readiness Check
            ready_resp = client.get(f"{base_url}/health/ready")
            ready_data = ready_resp.json()

            # 3. Root Endpoint Check
            root_resp = client.get(f"{base_url}/")
            root_data = root_resp.json()

            status_ok = (
                live_resp.status_code == 200
                and ready_resp.status_code == 200
                and root_resp.status_code == 200
                and live_data.get("service") == expected_name
                and ready_data.get("status") == "ready"
                and corr_returned == custom_trace_id
            )

            if status_ok:
                print(
                    f"[PASS] Port {port:<4} | {expected_name:<22} | "
                    f"Live: {live_data['status']} | Ready: {ready_data['status']} | Corr: {corr_returned}"
                )
            else:
                print(f"[FAIL] Port {port:<4} | {expected_name} unexpected payload: {live_data}")
                all_passed = False

        except Exception as e:
            print(f"[FAIL] Port {port:<4} | {expected_name} connection failed: {e}")
            all_passed = False

if not all_passed:
    sys.exit(1)

print("\n>>> All 6 microservices successfully verified over live HTTP! <<<")
