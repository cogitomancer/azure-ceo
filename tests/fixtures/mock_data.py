"""
Mock data for testing.
"""

MOCK_SEGMENT = {
    "id": "seg_test123",
    "name": "Test Segment",
    "size": 1000,
    "criteria": {"category": "test"}
}

MOCK_CAMPAIGN = {
    "id": "camp_test123",
    "name": "Test Campaign",
    "objective": "Test objective",
    "status": "draft"
}

MOCK_MESSAGE_VARIANTS = [
    {
        "variant_name": "A",
        "subject": "Test Subject A",
        "body": "Test body A with citation [Source: Test Doc, Page 1]"
    },
    {
        "variant_name": "B",
        "subject": "Test Subject B",
        "body": "Test body B with citation [Source: Test Doc, Page 2]"
    }
]