def test_generate_template(client):
    resp = client.post("/templates/generate", json={
        "target_role": "Finance Analyst",
        "department": "Finance",
        "seniority": "mid",
        "company_context": "a mid-size fintech company",
        "difficulty_level": "medium",
        "push_to_gophish": False,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "subject" in data and data["subject"]
    assert "{{.URL}}" in data["html_body"]
    assert data["model_used"] == "mock"
    assert data["gophish_template_id"] is None  # Gophish not configured -> stays unset


def test_list_and_get_template(client):
    create = client.post("/templates/generate", json={
        "target_role": "Engineer", "department": "Engineering",
    }).json()
    listed = client.get("/templates").json()
    assert any(t["id"] == create["id"] for t in listed)

    fetched = client.get(f"/templates/{create['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == create["id"]


def test_campaign_requires_approval_before_launch(client):
    tmpl = client.post("/templates/generate", json={
        "target_role": "Sales Rep", "department": "Sales",
    }).json()
    campaign = client.post("/campaigns", json={
        "name": "Sales Test", "template_id": tmpl["id"], "department": "Sales",
    }).json()
    assert campaign["status"] == "draft"

    # Launch without approval must fail.
    blocked = client.post(f"/campaigns/{campaign['id']}/launch")
    assert blocked.status_code == 400

    approved = client.post(f"/campaigns/{campaign['id']}/approve",
                            json={"approved_by": "security-lead@company.com"})
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    launched = client.post(f"/campaigns/{campaign['id']}/launch")
    assert launched.status_code == 200
    assert launched.json()["status"] == "launched"
