from unittest.mock import AsyncMock

import pytest

from src.user.application.commands import (
    DeleteAccountCommand,
    UpdateFitnessCommand,
    UpdateUserInfoCommand,
)
from src.user.application.handlers.delete_account import DeleteAccountCommandHandler
from src.user.application.handlers.get_profile import GetMyProfileQueryHandler
from src.user.application.handlers.update_fitness import UpdateFitnessCommandHandler
from src.user.application.handlers.update_user_info import UpdateUserInfoCommandHandler
from src.user.application.queries import GetMyProfileQuery
from src.user.application.read_models import FitnessReadModel, FullProfileReadModel
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
def read_repo():
    return AsyncMock()


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


@pytest.fixture
def full_profile_read_model():
    return FullProfileReadModel(
        id=1,
        name="Test User",
        email="test@example.com",
        avatar_url=None,
        is_verified=True,
        is_2fa_enabled=False,
        oauth_provider=None,
        fitness=FitnessReadModel(
            weight=70.0,
            height=175.0,
            age=25,
            gender=Gender.MALE,
            fitness_goal=FitnessGoal.MUSCLE_GAIN,
            bmi=22.9,
        ),
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


class TestGetMyProfileQueryHandler:
    @pytest.fixture
    def handler(self, read_repo):
        return GetMyProfileQueryHandler(read_repo)

    @pytest.mark.asyncio
    async def test_get_profile_success(self, handler, read_repo, full_profile_read_model):
        read_repo.get_full_profile.return_value = full_profile_read_model

        result = await handler.handle(GetMyProfileQuery(user_id=1))

        assert result.id == 1
        assert result.name == "Test User"
        read_repo.get_full_profile.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_profile_not_found_raises(self, handler, read_repo):
        read_repo.get_full_profile.return_value = None

        with pytest.raises(UserNotFoundError):
            await handler.handle(GetMyProfileQuery(user_id=999))


class TestUpdateUserInfoCommandHandler:
    @pytest.fixture
    def handler(self, profile_repo):
        return UpdateUserInfoCommandHandler(profile_repo)

    @pytest.mark.asyncio
    async def test_update_info_returns_none(self, handler, profile_repo, profile):
        profile_repo.get_by_id.return_value = profile
        profile_repo.save_user_info.return_value = None

        result = await handler.handle(UpdateUserInfoCommand(user_id=1, name="New Name", avatar_url=None))

        assert result is None

    @pytest.mark.asyncio
    async def test_update_info_mutates_domain_before_save(self, handler, profile_repo, profile):
        profile_repo.get_by_id.return_value = profile
        profile_repo.save_user_info.return_value = None

        await handler.handle(UpdateUserInfoCommand(user_id=1, name="Changed", avatar_url=None))

        saved_name = profile_repo.save_user_info.call_args.args[1]
        assert saved_name == "Changed"

    @pytest.mark.asyncio
    async def test_update_info_avatar_url(self, handler, profile_repo, profile):
        profile_repo.get_by_id.return_value = profile
        profile_repo.save_user_info.return_value = None

        await handler.handle(UpdateUserInfoCommand(user_id=1, name=None, avatar_url="https://example.com/avatar.png"))

        _, _, avatar_arg = profile_repo.save_user_info.call_args.args
        assert avatar_arg == "https://example.com/avatar.png"

    @pytest.mark.asyncio
    async def test_update_info_user_not_found_raises(self, handler, profile_repo):
        profile_repo.get_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await handler.handle(UpdateUserInfoCommand(user_id=999, name="Name", avatar_url=None))

        profile_repo.save_user_info.assert_not_called()


class TestUpdateFitnessCommandHandler:
    @pytest.fixture
    def handler(self, profile_repo):
        return UpdateFitnessCommandHandler(profile_repo)

    @pytest.mark.asyncio
    async def test_update_fitness_returns_none(self, handler, profile_repo, profile):
        profile_repo.get_by_id.return_value = profile
        profile_repo.save_fitness.return_value = None

        result = await handler.handle(UpdateFitnessCommand(
            user_id=1, weight=80.0, height=180.0, age=30,
            gender=Gender.MALE, fitness_goal=FitnessGoal.STRENGTH_BUILDING,
        ))

        assert result is None

    @pytest.mark.asyncio
    async def test_update_fitness_mutates_domain_before_save(self, handler, profile_repo, profile):
        profile_repo.get_by_id.return_value = profile
        profile_repo.save_fitness.return_value = None

        await handler.handle(UpdateFitnessCommand(
            user_id=1, weight=99.0, height=None, age=None, gender=None, fitness_goal=None,
        ))

        saved_fitness: FitnessProfileDomain = profile_repo.save_fitness.call_args.args[1]
        assert saved_fitness.weight == 99.0
        assert saved_fitness.height == 175.0  # unchanged, came from domain object

    @pytest.mark.asyncio
    async def test_update_fitness_creates_profile_when_none(self, handler, profile_repo, profile_without_fitness):
        profile_repo.get_by_id.return_value = profile_without_fitness
        profile_repo.save_fitness.return_value = None

        await handler.handle(UpdateFitnessCommand(
            user_id=1, weight=70.0, height=175.0, age=25,
            gender=Gender.FEMALE, fitness_goal=FitnessGoal.ENDURANCE,
        ))

        profile_repo.save_fitness.assert_called_once()
        saved_fitness: FitnessProfileDomain = profile_repo.save_fitness.call_args.args[1]
        assert saved_fitness.weight == 70.0

    @pytest.mark.asyncio
    async def test_update_fitness_user_not_found_raises(self, handler, profile_repo):
        profile_repo.get_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await handler.handle(UpdateFitnessCommand(
                user_id=999, weight=70.0, height=175.0, age=25, gender=None, fitness_goal=None,
            ))

        profile_repo.save_fitness.assert_not_called()


class TestDeleteAccountCommandHandler:
    @pytest.fixture
    def handler(self, profile_repo):
        return DeleteAccountCommandHandler(profile_repo)

    @pytest.mark.asyncio
    async def test_delete_account_calls_deactivate(self, handler, profile_repo):
        await handler.handle(DeleteAccountCommand(user_id=1))

        profile_repo.deactivate.assert_called_once_with(1)