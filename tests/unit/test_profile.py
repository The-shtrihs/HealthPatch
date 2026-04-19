from unittest.mock import AsyncMock

import pytest

from src.user.application.dto import UpdateFitnessCommand, UpdateUserInfoCommand
from src.user.application.use_cases import UserProfileUseCases
from src.user.domain.errors import UserNotFoundError
from src.user.domain.models import (
    FitnessGoal,
    FitnessProfileDomain,
    Gender,
    UserProfileDomain,
)

@pytest.fixture
def profile_repo():
    return AsyncMock()


@pytest.fixture
def use_cases(profile_repo):
    return UserProfileUseCases(profile_repo)


@pytest.fixture
def fitness():
    return FitnessProfileDomain(
        weight=70.0,
        height=175.0,
        age=25,
        gender=Gender.MALE,
        fitness_goal=FitnessGoal.MUSCLE_GAIN,
    )


@pytest.fixture
def profile(fitness):
    return UserProfileDomain(
        id=1,
        name="Test User",
        email="test@example.com",
        avatar_url=None,
        is_verified=True,
        is_active=True,
        is_2fa_enabled=False,
        oauth_provider=None,
        fitness=fitness,
    )


@pytest.fixture
def profile_without_fitness():
    return UserProfileDomain(
        id=1,
        name="Test User",
        email="test@example.com",
        avatar_url=None,
        is_verified=True,
        is_active=True,
        is_2fa_enabled=False,
        oauth_provider=None,
        fitness=None,
    )


class TestFitnessProfileDomain:
    def test_calc_bmi_returns_correct_value(self, fitness):
        bmi = fitness.calc_bmi()
        assert bmi is not None
        assert abs(bmi - 22.9) < 0.1

    def test_calc_bmi_returns_none_when_weight_missing(self):
        f = FitnessProfileDomain(weight=None, height=175.0, age=25, gender=None, fitness_goal=None)
        assert f.calc_bmi() is None

    def test_calc_bmi_returns_none_when_height_missing(self):
        f = FitnessProfileDomain(weight=70.0, height=None, age=25, gender=None, fitness_goal=None)
        assert f.calc_bmi() is None

    def test_calc_bmi_returns_none_when_height_zero(self):
        f = FitnessProfileDomain(weight=70.0, height=0.0, age=25, gender=None, fitness_goal=None)
        assert f.calc_bmi() is None

class TestUserProfileDomain:
    def test_update_info_changes_name(self, profile):
        profile.update_info(name="New Name")
        assert profile.name == "New Name"

    def test_update_info_changes_avatar_url(self, profile):
        profile.update_info(avatar_url="https://cdn.example.com/avatar.png")
        assert profile.avatar_url == "https://cdn.example.com/avatar.png"

    def test_update_info_none_values_do_not_overwrite(self, profile):
        original_name = profile.name
        profile.update_info(name=None)
        assert profile.name == original_name

    def test_update_fitness_creates_new_profile_when_none(self, profile_without_fitness):
        profile_without_fitness.update_fitness(weight=80.0, height=180.0)
        assert profile_without_fitness.fitness is not None
        assert profile_without_fitness.fitness.weight == 80.0

    def test_update_fitness_patches_existing_fields(self, profile):
        profile.update_fitness(weight=90.0)
        assert profile.fitness.weight == 90.0
        assert profile.fitness.height == 175.0  # unchanged

    def test_deactivate_sets_is_active_false(self, profile):
        profile.deactivate()
        assert profile.is_active is False


class TestGetProfile:
    @pytest.mark.asyncio
    async def test_get_profile_success(self, use_cases, profile_repo, profile):
        profile_repo.get_full_profile.return_value = profile

        result = await use_cases.get_profile(1)

        assert result.id == 1
        assert result.name == "Test User"
        profile_repo.get_full_profile.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_profile_not_found_raises(self, use_cases, profile_repo):
        profile_repo.get_full_profile.return_value = None

        with pytest.raises(UserNotFoundError):
            await use_cases.get_profile(999)


class TestUpdateInfo:
    @pytest.mark.asyncio
    async def test_update_info_name(self, use_cases, profile_repo, profile):
        updated_profile = UserProfileDomain(
            id=profile.id, name="New Name", email=profile.email,
            avatar_url=profile.avatar_url, is_verified=profile.is_verified,
            is_active=profile.is_active, is_2fa_enabled=profile.is_2fa_enabled,
            oauth_provider=profile.oauth_provider, fitness=profile.fitness,
        )
        profile_repo.get_full_profile.return_value = profile
        profile_repo.save_user_info.return_value = updated_profile

        result = await use_cases.update_info(1, UpdateUserInfoCommand(name="New Name", avatar_url=None))

        profile_repo.save_user_info.assert_called_once_with(1, "New Name", None)
        assert result.name == "New Name"

    @pytest.mark.asyncio
    async def test_update_info_avatar_url(self, use_cases, profile_repo, profile):
        profile_repo.get_full_profile.return_value = profile
        profile_repo.save_user_info.return_value = profile

        await use_cases.update_info(
            1,
            UpdateUserInfoCommand(name=None, avatar_url="https://example.com/avatar.png"),
        )

        _, _, avatar_arg = profile_repo.save_user_info.call_args.args
        assert avatar_arg == "https://example.com/avatar.png"

    @pytest.mark.asyncio
    async def test_update_info_user_not_found_raises(self, use_cases, profile_repo):
        profile_repo.get_full_profile.return_value = None

        with pytest.raises(UserNotFoundError):
            await use_cases.update_info(999, UpdateUserInfoCommand(name="Name", avatar_url=None))

        profile_repo.save_user_info.assert_not_called()


class TestUpdateFitness:
    @pytest.mark.asyncio
    async def test_update_fitness_success(self, use_cases, profile_repo, profile):
        profile_repo.get_full_profile.return_value = profile
        profile_repo.save_fitness.return_value = profile.fitness

        cmd = UpdateFitnessCommand(
            weight=80.0, height=180.0, age=30,
            gender=Gender.MALE, fitness_goal=FitnessGoal.STRENGTH_BUILDING,
        )
        result = await use_cases.update_fitness(1, cmd)

        profile_repo.save_fitness.assert_called_once()
        assert result is profile.fitness

    @pytest.mark.asyncio
    async def test_update_fitness_creates_profile_when_none(self, use_cases, profile_repo, profile_without_fitness):
        new_fitness = FitnessProfileDomain(
            weight=70.0, height=175.0, age=25,
            gender=Gender.FEMALE, fitness_goal=FitnessGoal.ENDURANCE,
        )
        profile_repo.get_full_profile.return_value = profile_without_fitness
        profile_repo.save_fitness.return_value = new_fitness

        cmd = UpdateFitnessCommand(
            weight=70.0, height=175.0, age=25,
            gender=Gender.FEMALE, fitness_goal=FitnessGoal.ENDURANCE,
        )
        result = await use_cases.update_fitness(1, cmd)

        profile_repo.save_fitness.assert_called_once()
        assert result is not None

    @pytest.mark.asyncio
    async def test_update_fitness_user_not_found_raises(self, use_cases, profile_repo):
        profile_repo.get_full_profile.return_value = None

        cmd = UpdateFitnessCommand(weight=70.0, height=175.0, age=25, gender=None, fitness_goal=None)
        with pytest.raises(UserNotFoundError):
            await use_cases.update_fitness(999, cmd)

        profile_repo.save_fitness.assert_not_called()


class TestDeleteAccount:
    @pytest.mark.asyncio
    async def test_delete_account_calls_deactivate(self, use_cases, profile_repo):
        await use_cases.delete_account(1)

        profile_repo.deactivate.assert_called_once_with(1)