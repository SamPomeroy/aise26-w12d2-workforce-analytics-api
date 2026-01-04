import pytest
from fastapi import status


@pytest.mark.integration
class TestIntegration:
    """integration tests for complete workflows"""
    
    def test_complete_job_posting_workflow(self, client, db):
        """test complete workflow: register employer, login, create job, update, deactivate"""
        # register employer
        register_response = client.post(
            "/v1/auth/register",
            json={
                "email": "workflow@example.com",
                "username": "workflowemployer",
                "password": "WorkflowPass123",
                "full_name": "Workflow Employer",
                "role": "employer"
            }
        )
        assert register_response.status_code == status.HTTP_201_CREATED
        
        # login
        login_response = client.post(
            "/v1/auth/login",
            json={
                "username": "workflowemployer",
                "password": "WorkflowPass123"
            }
        )
        assert login_response.status_code == status.HTTP_200_OK
        token = login_response.json()["access_token"]
        
        # create job
        job_data = {
            "title": "Software Engineer",
            "company": "Tech Startup",
            "location": "Remote",
            "employment_type": "full-time",
            "experience_level": "mid",
            "salary_min": 80000,
            "salary_max": 120000,
            "required_skills": ["python", "javascript"]
        }
        create_response = client.post(
            "/v1/jobs/",
            json=job_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        job_id = create_response.json()["id"]
        
        # update job
        update_response = client.put(
            f"/v1/jobs/{job_id}",
            json={"title": "Senior Software Engineer"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.json()["title"] == "Senior Software Engineer"
        
        # deactivate job
        deactivate_response = client.patch(
            f"/v1/jobs/{job_id}/deactivate",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert deactivate_response.status_code == status.HTTP_200_OK
        assert deactivate_response.json()["is_active"] is False
    
    def test_job_search_and_filter_workflow(self, client, db, test_employer):
        """test searching and filtering jobs"""
        # create multiple jobs with different attributes
        from app.models.job_posting import JobPosting
        
        jobs_data = [
            {"title": "Python Dev", "company": "CompanyA", "location": "NYC", "remote_allowed": False, "salary_min": 100000},
            {"title": "Remote Python", "company": "CompanyB", "location": "Remote", "remote_allowed": True, "salary_min": 90000},
            {"title": "JS Developer", "company": "CompanyC", "location": "SF", "remote_allowed": False, "salary_min": 110000},
        ]
        
        for job_data in jobs_data:
            job = JobPosting(
                **job_data,
                employment_type="full-time",
                experience_level="mid",
                posted_by_user_id=test_employer.id
            )
            db.add(job)
        db.commit()
        
        # test remote filter
        response = client.get("/v1/jobs/?remote_only=true")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(job["remote_allowed"] for job in data["jobs"])
        
        # test salary filter
        response = client.get("/v1/jobs/?min_salary=100000")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for job in data["jobs"]:
            if job["salary_min"]:
                assert job["salary_min"] >= 100000
    
    def test_root_and_version_endpoints(self, client):
        """test root and version info endpoints"""
        # test root
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "version" in data
        assert "status" in data
        
        # test v1 info
        response = client.get("/v1")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "endpoints" in data
    
    def test_skill_demand_filtering(self, client, db):
        """test skill demand score filtering"""
        from app.models.skill import Skill
        
        skills = [
            Skill(name="HighDemand1", category="technical", demand_score=95.0),
            Skill(name="HighDemand2", category="technical", demand_score=90.0),
            Skill(name="MedDemand", category="technical", demand_score=60.0),
            Skill(name="LowDemand", category="technical", demand_score=20.0),
        ]
        for skill in skills:
            db.add(skill)
        db.commit()
        
        # test min demand filter
        response = client.get("/v1/skills/?min_demand=85")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["skills"]) == 2
        assert all(s["demand_score"] >= 85 for s in data["skills"])
    
    def test_search_skills_by_name(self, client, db):
        """test searching skills by name"""
        from app.models.skill import Skill
        
        skills = [
            Skill(name="Python Programming", category="technical", demand_score=90.0, description="python language"),
            Skill(name="JavaScript", category="technical", demand_score=85.0, description="js language"),
            Skill(name="Python Django", category="technical", demand_score=80.0, description="python framework"),
        ]
        for skill in skills:
            db.add(skill)
        db.commit()
        
        # search for python
        response = client.get("/v1/skills/?search=python")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["skills"]) >= 2
        for skill in data["skills"]:
            assert "python" in skill["name"].lower() or "python" in skill["description"].lower()
