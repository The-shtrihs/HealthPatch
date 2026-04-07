from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.exceptions import NotFoundError
from src.models.user import FitnessGoal, Gender, User, UserProfile
from src.schemas.profile import FitnessProfileUpdate, UserInfoUpdate
from src.services.profile import ProfileService, _build_fitness_response, _calc_bmi


@pytest.fixture
def profile_repo():
    return AsyncMock()


@pytest.fixture
def profile_service(profile_repo):
    return ProfileService(profile_repo)


@pytest.fixture
def active_user():
    u = MagicMock(spec=User)
    u.id = 1
    u.name = "Test User"
    u.email = "test@example.com"
    u.avatar_url = None
    u.is_verified = True
    u.is_2fa_enabled = False
    u.oauth_provider = None
    u.profile = None
    return u


@pytest.fixture
def fitness_profile():
    p = MagicMock(spec=UserProfile)
    p.weight = 70.0
    p.height = 175.0
    p.age = 25
    p.gender = Gender.MALE
    p.fitness_goal = FitnessGoal.MUSCLE_GAIN
    return p


@pytest.fixture
def user_with_profile(active_user, fitness_profile):
    active_user.profile = fitness_profile
    return active_user

class TestCalcBmi:
    def test_standard_values(self):
        assert _calc_bmi(70.0, 175.0) == 22.9

    def test_none_weight_returns_none(self):
        assert _calc_bmi(None, 175.0) is None

    def test_none_height_returns_none(self):
        assert _calc_bmi(70.0, None) is None

    def test_zero_height_returns_none(self):
        assert _calc_bmi(70.0, 0.0) is None

    def test_both_none_returns_none(self):
        assert _calc_bmi(None, None) is None

    def test_result_is_rounded_to_one_decimal(self):
        result = _calc_bmi(80.0, 180.0)
        assert result is not None
        assert result == round(result, 1)

    def test_underweight_range(self):
        result = _calc_bmi(45.0, 170.0)
        assert result is not None
        assert result < 18.5

    def test_obese_range(self):
        result = _calc_bmi(120.0, 170.0)
        assert result is not None
        assert result >= 30.0


class TestBuildFitnessResponse:
    def test_none_profile_returns_none(self):
        assert _build_fitness_response(None) is None

    def test_with_full_profile_maps_all_fields(self, fitness_profile):
        result = _build_fitness_response(fitness_profile)
        assert result is not None
        assert result.weight == fitness_profile.weight
        assert result.height == fitness_profile.height
        assert result.age == fitness_profile.age
        assert result.gender == fitness_profile.gender
        assert result.fitness_goal == fitness_profile.fitness_goal

    def test_bmi_calculated_when_both_present(self, fitness_profile):
        result = _build_fitness_response(fitness_profile)
        assert result.bmi == _calc_bmi(70.0, 175.0)

    def test_bmi_none_when_weight_missing(self, fitness_profile):
        fitness_profile.weight = None
        result = _build_fitness_response(fitness_profile)
        assert result.bmi is None

    def test_bmi_none_when_height_missing(self, fitness_profile):
        fitness_profile.height = None
        result = _build_fitness_response(fitness_profile)
        assert result.bmi is None


class TestGetFullProfile:
    @pytest.mark.asyncio
    async def test_success_with_fitness_profile(self, profile_service, profile_repo, user_with_profile, fitness_profile):
        profile_repo.get_full_user.return_value = user_with_profile

        result = await profile_service.get_full_profile(1)

        profile_repo.get_full_user.assert_called_once_with(1)
        assert result.id == user_with_profile.id
        assert result.email == user_with_profile.email
        assert result.profile is not None
        assert result.profile.weight == fitness_profile.weight

    @pytest.mark.asyncio
    async def test_success_without_fitness_profile(self, profile_service, profile_repo, active_user):
        active_user.profile = None
        profile_repo.get_full_user.return_value = active_user

        result = await profile_service.get_full_profile(1)

        assert result.profile is None

    @pytest.mark.asyncio
    async def test_user_not_found_raises(self, profile_service, profile_repo):
        profile_repo.get_full_user.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            await profile_service.get_full_profile(999)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_user_not_found_does_not_build_response(self, profile_service, profile_repo):
        profile_repo.get_full_user.return_value = None

        with pytest.raises(NotFoundError):
            await profile_service.get_full_profile(999)

        profile_repo.get_full_user.assert_called_once()

class TestUpdateUserInfo:
    @pytest.mark.asyncio
    async def test_with_name_calls_repo(self, profile_service, profile_repo, active_user):
        data = UserInfoUpdate(name="New Name")
        profile_repo.update_user_info.return_value = active_user
        profile_repo.get_full_user.return_value = active_user

        await profile_service.update_user_info(active_user, data)

        profile_repo.update_user_info.assert_called_once_with(user=active_user, data=data)

    @pytest.mark.asyncio
    async def test_with_avatar_calls_repo(self, profile_service, profile_repo, active_user):
        data = UserInfoUpdate(avatar_url="https://example.com/avatar.png")
        profile_repo.update_user_info.return_value = active_user
        profile_repo.get_full_user.return_value = active_user

        await profile_service.update_user_info(active_user, data)

        profile_repo.update_user_info.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_data_skips_repo(self, profile_service, profile_repo, active_user):
        data = UserInfoUpdate()  
        profile_repo.get_full_user.return_value = active_user

        await profile_service.update_user_info(active_user, data)

        profile_repo.update_user_info.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_data_still_returns_profile(self, profile_service, profile_repo, active_user):
        data = UserInfoUpdate()
        profile_repo.get_full_user.return_value = active_user

        result = await profile_service.update_user_info(active_user, data)

        assert result is not None
        assert result.id == active_user.id

    @pytest.mark.asyncio
    async def test_empty_data_fetches_fresh_profile(self, profile_service, profile_repo, active_user):
        data = UserInfoUpdate()
        profile_repo.get_full_user.return_value = active_user

        await profile_service.update_user_info(active_user, data)

        profile_repo.get_full_user.assert_called_once_with(active_user.id)



class TestUpdateFitnessProfile:
    @pytest.mark.asyncio
    async def test_success_returns_response(self, profile_service, profile_repo, fitness_profile):
        fitness_profile.weight = 80.0
        fitness_profile.height = 180.0
        profile_repo.update_fitness_profile.return_value = fitness_profile
        data = FitnessProfileUpdate(weight=80.0, height=180.0)

        result = await profile_service.update_fitness_profile(1, data)

        profile_repo.update_fitness_profile.assert_called_once_with(user_id=1, data=data)
        assert result.weight == 80.0
        assert result.height == 180.0

    @pytest.mark.asyncio
    async def test_bmi_calculated_in_response(self, profile_service, profile_repo, fitness_profile):
        fitness_profile.weight = 70.0
        fitness_profile.height = 175.0
        profile_repo.update_fitness_profile.return_value = fitness_profile
        data = FitnessProfileUpdate(weight=70.0, height=175.0)

        result = await profile_service.update_fitness_profile(1, data)

        assert result.bmi == 22.9

    @pytest.mark.asyncio
    async def test_bmi_none_without_height(self, profile_service, profile_repo, fitness_profile):
        fitness_profile.weight = 70.0
        fitness_profile.height = None
        profile_repo.update_fitness_profile.return_value = fitness_profile
        data = FitnessProfileUpdate(weight=70.0)

        result = await profile_service.update_fitness_profile(1, data)

        assert result.bmi is None

    @pytest.mark.asyncio
    async def test_partial_update_only_sets_provided_field(self, profile_service, profile_repo, fitness_profile):
        fitness_profile.weight = 75.0
        profile_repo.update_fitness_profile.return_value = fitness_profile
        data = FitnessProfileUpdate(weight=75.0)

        result = await profile_service.update_fitness_profile(1, data)

        assert result.weight == 75.0

    @pytest.mark.asyncio
    async def test_repo_error_propagates(self, profile_service, profile_repo):
        profile_repo.update_fitness_profile.side_effect = RuntimeError("DB error")
        data = FitnessProfileUpdate(weight=70.0)

        with pytest.raises(RuntimeError, match="DB error"):
            await profile_service.update_fitness_profile(1, data)


class TestDeleteAccount:
    @pytest.mark.asyncio
    async def test_delete_calls_deactivate(self, profile_service, profile_repo, active_user):
        await profile_service.delete_account(active_user)

        profile_repo.deactivate_user.assert_called_once_with(active_user)

    @pytest.mark.asyncio
    async def test_delete_passes_correct_user(self, profile_service, profile_repo, active_user):
        other_user = MagicMock(spec=User, id=99)

        await profile_service.delete_account(other_user)

        profile_repo.deactivate_user.assert_called_once_with(other_user)

    @pytest.mark.asyncio
    async def test_deactivate_repo_error_propagates(self, profile_service, profile_repo, active_user):
        profile_repo.deactivate_user.side_effect = RuntimeError("DB gone")

        with pytest.raises(RuntimeError, match="DB gone"):
            await profile_service.delete_account(active_user)