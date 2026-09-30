import json
import pytest
from pathlib import Path
from src.core.domain.models import CourseProfile, DocumentType, NotionTarget
from src.adapters.outbound.json_course_profile_repository import JsonCourseProfileRepository

@pytest.fixture
def repo_file(tmp_path):
    return tmp_path / "course_profiles.json"

@pytest.fixture
def sample_profile():
    return CourseProfile(
        subject="Statistical Modelling",
        professor_type="PhD Professor in Statistical Modelling",
        doc_type=DocumentType.SLIDES,
        folder_path=Path("/tmp/stats_slides"),
        target=NotionTarget(
            database_id="db_stats_123",
            course_name="Statistical Modelling",
            database_title="Notes",
        ),
    )

def test_repo_empty_on_missing_file(repo_file):
    repo = JsonCourseProfileRepository(file_path=repo_file)
    assert repo.list_profiles() == []
    assert repo.get_profile("Statistical Modelling") is None

def test_repo_save_and_get_profile(repo_file, sample_profile):
    repo = JsonCourseProfileRepository(file_path=repo_file)
    repo.save_profile(sample_profile)

    assert repo_file.exists()

    # Retrieve by subject name
    fetched = repo.get_profile("Statistical Modelling")
    assert fetched is not None
    assert fetched.subject == "Statistical Modelling"
    assert fetched.professor_type == "PhD Professor in Statistical Modelling"
    assert fetched.doc_type == DocumentType.SLIDES
    assert fetched.folder_path == Path("/tmp/stats_slides")
    assert fetched.target.database_id == "db_stats_123"

    # Retrieve by normalized key
    by_key = repo.get_profile("statistical_modelling")
    assert by_key is not None
    assert by_key.subject == "Statistical Modelling"

    # Retrieve case-insensitive
    by_case = repo.get_profile("statistical modelling")
    assert by_case is not None

def test_repo_list_profiles_sorted(repo_file):
    repo = JsonCourseProfileRepository(file_path=repo_file)

    p1 = CourseProfile(
        subject="Text Mining",
        professor_type="PhD",
        doc_type=DocumentType.SLIDES,
        folder_path=Path("/tmp/tm"),
        target=NotionTarget(database_id="db2", course_name="TM", database_title="Notes"),
    )
    p2 = CourseProfile(
        subject="Applied Econometrics",
        professor_type="PhD",
        doc_type=DocumentType.PAPER_OR_BOOK,
        folder_path=Path("/tmp/econ"),
        target=NotionTarget(database_id="db1", course_name="Econ", database_title="Notes"),
    )

    repo.save_profile(p1)
    repo.save_profile(p2)

    profiles = repo.list_profiles()
    assert len(profiles) == 2
    assert profiles[0].subject == "Applied Econometrics"
    assert profiles[1].subject == "Text Mining"

def test_repo_delete_profile(repo_file, sample_profile):
    repo = JsonCourseProfileRepository(file_path=repo_file)
    repo.save_profile(sample_profile)

    assert repo.get_profile("Statistical Modelling") is not None
    deleted = repo.delete_profile("Statistical Modelling")
    assert deleted is True
    assert repo.get_profile("Statistical Modelling") is None
    assert repo.list_profiles() == []
