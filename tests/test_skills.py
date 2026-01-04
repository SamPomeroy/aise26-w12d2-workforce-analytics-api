import pytest
from fastapi import status
from app.models.skill import Skill


@pytest.mark.skills
class TestSkills:
    """test skills endpoints"""
    
    @pytest.fixture
    def sample_skill_data(self):
        """sample skill data"""
        return {
            "name": "Python",
            "category": "technical",
            "description": "programming language",
            "demand_score": 85.5,
            "growth_rate": 12.3
        }
    
    def test_create_skill_as_admin(self, client, admin_token, sample_skill_data):
        """test admin can create skill"""
        response = client.post(
            "/v1/skills/",
            json=sample_skill_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == sample_skill_data["name"]
        assert data["demand_score"] == sample_skill_data["demand_score"]
    
    def test_create_skill_as_user_fails(self, client, user_token, sample_skill_data):
        """test regular user cannot create skill"""
        response = client.post(
            "/v1/skills/",
            json=sample_skill_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_create_duplicate_skill(self, client, db, admin_token):
        """test creating duplicate skill fails"""
        skill = Skill(name="Python", category="technical", demand_score=80.0)
        db.add(skill)
        db.commit()
        
        response = client.post(
            "/v1/skills/",
            json={"name": "Python", "category": "technical", "demand_score": 85.0},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_list_skills_public(self, client, db):
        """test listing skills works without auth"""
        skill = Skill(name="JavaScript", category="technical", demand_score=75.0)
        db.add(skill)
        db.commit()
        
        response = client.get("/v1/skills/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 1
    
    def test_list_skills_pagination(self, client, db):
        """test skills pagination"""
        for i in range(25):
            skill = Skill(name=f"Skill{i}", category="technical", demand_score=float(i))
            db.add(skill)
        db.commit()
        
        response = client.get("/v1/skills/?skip=0&limit=20")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["skills"]) == 20
        assert data["total"] >= 25
    
    def test_list_skills_filter_category(self, client, db):
        """test filtering skills by category"""
        skill1 = Skill(name="Python", category="technical", demand_score=80.0)
        skill2 = Skill(name="Communication", category="soft", demand_score=70.0)
        db.add_all([skill1, skill2])
        db.commit()
        
        response = client.get("/v1/skills/?category=technical")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(skill["category"] == "technical" for skill in data["skills"])
    
    def test_list_skills_min_demand(self, client, db):
        """test filtering skills by minimum demand score"""
        skill1 = Skill(name="HighDemand", category="technical", demand_score=90.0)
        skill2 = Skill(name="LowDemand", category="technical", demand_score=30.0)
        db.add_all([skill1, skill2])
        db.commit()
        
        response = client.get("/v1/skills/?min_demand=80")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(skill["demand_score"] >= 80 for skill in data["skills"])
    
    def test_get_skill_by_id(self, client, db):
        """test getting specific skill by id"""
        skill = Skill(name="Docker", category="technical", demand_score=78.0)
        db.add(skill)
        db.commit()
        db.refresh(skill)
        
        response = client.get(f"/v1/skills/{skill.id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Docker"
    
    def test_get_skill_by_name(self, client, db):
        """test getting skill by name"""
        skill = Skill(name="Kubernetes", category="technical", demand_score=82.0)
        db.add(skill)
        db.commit()
        
        response = client.get("/v1/skills/name/Kubernetes")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"].lower() == "kubernetes".lower()
    
    def test_update_skill_as_admin(self, client, db, admin_token):
        """test admin can update skill"""
        skill = Skill(name="React", category="technical", demand_score=75.0)
        db.add(skill)
        db.commit()
        db.refresh(skill)
        
        response = client.put(
            f"/v1/skills/{skill.id}",
            json={"demand_score": 85.0},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["demand_score"] == 85.0
    
    def test_update_skill_as_user_fails(self, client, db, user_token):
        """test user cannot update skill"""
        skill = Skill(name="Vue", category="technical", demand_score=70.0)
        db.add(skill)
        db.commit()
        db.refresh(skill)
        
        response = client.put(
            f"/v1/skills/{skill.id}",
            json={"demand_score": 80.0},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_delete_skill_as_admin(self, client, db, admin_token):
        """test admin can delete skill"""
        skill = Skill(name="Obsolete", category="technical", demand_score=10.0)
        db.add(skill)
        db.commit()
        db.refresh(skill)
        
        response = client.delete(
            f"/v1/skills/{skill.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    def test_get_trending_skills(self, client, db):
        """test getting top trending skills"""
        for i in range(15):
            skill = Skill(
                name=f"Skill{i}",
                category="technical",
                demand_score=float(100 - i),
                growth_rate=float(i)
            )
            db.add(skill)
        db.commit()
        
        response = client.get("/v1/skills/trending/top?limit=10")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["skills"]) == 10
        # verify sorted by demand score descending
        scores = [s["demand_score"] for s in data["skills"]]
        assert scores == sorted(scores, reverse=True)
