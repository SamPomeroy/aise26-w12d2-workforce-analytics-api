import pytest
from fastapi import status
from app.models.job_posting import JobPosting


@pytest.mark.jobs
class TestJobPostings:
    """test job posting endpoints"""
    
    @pytest.fixture
    def sample_job_data(self):
        """sample job posting data"""
        return {
            "title": "Senior Python Developer",
            "company": "Tech Corp",
            "location": "San Francisco, CA",
            "description": "looking for experienced python developer",
            "employment_type": "full-time",
            "experience_level": "senior",
            "salary_min": 120000,
            "salary_max": 180000,
            "required_skills": ["python", "fastapi", "postgresql"],
            "preferred_skills": ["docker", "kubernetes"],
            "remote_allowed": True
        }
    
    def test_create_job_as_employer(self, client, employer_token, sample_job_data):
        """test employer can create job posting"""
        response = client.post(
            "/v1/jobs/",
            json=sample_job_data,
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == sample_job_data["title"]
        assert data["company"] == sample_job_data["company"]
    
    def test_create_job_as_admin(self, client, admin_token, sample_job_data):
        """test admin can create job posting"""
        response = client.post(
            "/v1/jobs/",
            json=sample_job_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_create_job_as_user_fails(self, client, user_token, sample_job_data):
        """test regular user cannot create job posting"""
        response = client.post(
            "/v1/jobs/",
            json=sample_job_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_job_no_auth(self, client, sample_job_data):
        """test creating job without auth fails"""
        response = client.post("/v1/jobs/", json=sample_job_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_jobs_public(self, client, db, test_employer):
        """test listing jobs works without auth"""
        # create test job
        job = JobPosting(
            title="Test Job",
            company="Test Company",
            location="Remote",
            employment_type="full-time",
            experience_level="mid",
            posted_by_user_id=test_employer.id
        )
        db.add(job)
        db.commit()
        
        response = client.get("/v1/jobs/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 1
        assert len(data["jobs"]) >= 1
    
    def test_list_jobs_pagination(self, client, db, test_employer):
        """test job listing pagination"""
        # create multiple jobs
        for i in range(15):
            job = JobPosting(
                title=f"Job {i}",
                company="Test Company",
                location="Remote",
                employment_type="full-time",
                experience_level="mid",
                posted_by_user_id=test_employer.id
            )
            db.add(job)
        db.commit()
        
        response = client.get("/v1/jobs/?skip=0&limit=10")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["jobs"]) == 10
        assert data["total"] >= 15
    
    def test_list_jobs_filter_company(self, client, db, test_employer):
        """test filtering jobs by company"""
        job1 = JobPosting(
            title="Job 1", company="Company A", location="Remote",
            employment_type="full-time", experience_level="mid",
            posted_by_user_id=test_employer.id
        )
        job2 = JobPosting(
            title="Job 2", company="Company B", location="Remote",
            employment_type="full-time", experience_level="mid",
            posted_by_user_id=test_employer.id
        )
        db.add_all([job1, job2])
        db.commit()
        
        response = client.get("/v1/jobs/?company=Company A")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all("Company A" in job["company"] for job in data["jobs"])
    
    def test_get_job_by_id(self, client, db, test_employer):
        """test getting specific job by id"""
        job = JobPosting(
            title="Test Job",
            company="Test Company",
            location="Remote",
            employment_type="full-time",
            experience_level="mid",
            posted_by_user_id=test_employer.id
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        response = client.get(f"/v1/jobs/{job.id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == job.id
        assert data["title"] == job.title
    
    def test_get_nonexistent_job(self, client):
        """test getting nonexistent job returns 404"""
        response = client.get("/v1/jobs/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_own_job(self, client, db, test_employer, employer_token):
        """test employer can update their own job"""
        job = JobPosting(
            title="Original Title",
            company="Test Company",
            location="Remote",
            employment_type="full-time",
            experience_level="mid",
            posted_by_user_id=test_employer.id
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        response = client.put(
            f"/v1/jobs/{job.id}",
            json={"title": "Updated Title"},
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Updated Title"
    
    def test_update_others_job_fails(self, client, db, test_employer, user_token):
        """test user cannot update someone else's job"""
        job = JobPosting(
            title="Test Job",
            company="Test Company",
            location="Remote",
            employment_type="full-time",
            experience_level="mid",
            posted_by_user_id=test_employer.id
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        response = client.put(
            f"/v1/jobs/{job.id}",
            json={"title": "Hacked Title"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_admin_can_update_any_job(self, client, db, test_employer, admin_token):
        """test admin can update any job"""
        job = JobPosting(
            title="Original Title",
            company="Test Company",
            location="Remote",
            employment_type="full-time",
            experience_level="mid",
            posted_by_user_id=test_employer.id
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        response = client.put(
            f"/v1/jobs/{job.id}",
            json={"title": "Admin Updated"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
    
    def test_deactivate_job(self, client, db, test_employer, employer_token):
        """test deactivating job posting"""
        job = JobPosting(
            title="Test Job",
            company="Test Company",
            location="Remote",
            employment_type="full-time",
            experience_level="mid",
            posted_by_user_id=test_employer.id,
            is_active=True
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        response = client.patch(
            f"/v1/jobs/{job.id}/deactivate",
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_active"] is False
    
    def test_delete_job_admin_only(self, client, db, test_employer, admin_token):
        """test only admin can permanently delete jobs"""
        job = JobPosting(
            title="Test Job",
            company="Test Company",
            location="Remote",
            employment_type="full-time",
            experience_level="mid",
            posted_by_user_id=test_employer.id
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        response = client.delete(
            f"/v1/jobs/{job.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
