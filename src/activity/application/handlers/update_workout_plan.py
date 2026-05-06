from src.activity.application.commands import UpdateWorkoutPlanCommand
from src.activity.domain.errors import NotResourceOwnerError, WorkoutPlanNotFoundError
from src.activity.domain.events import WorkoutPlanMadePublic
from src.activity.domain.interfaces import IActivityUnitOfWork


class UpdateWorkoutPlanCommandHandler:
    def __init__(self, uow: IActivityUnitOfWork):
        self._uow = uow

    async def handle(self, cmd: UpdateWorkoutPlanCommand) -> None:
        async with self._uow:
            plan = await self._uow.repo.get_plan_by_id(cmd.plan_id)
            if plan is None:
                raise WorkoutPlanNotFoundError(cmd.plan_id)
            if not plan.is_owned_by(cmd.user_id):
                raise NotResourceOwnerError("You do not own this workout plan")

            was_private = not plan.is_public
            plan.update_details(
                title=cmd.title,
                description=cmd.description,
                is_public=cmd.is_public,
            )
            await self._uow.repo.save_plan(plan)

            if was_private and plan.is_public:
                self._uow.events.append(
                    WorkoutPlanMadePublic(
                        plan_id=plan.id,
                        author_id=plan.author_id,
                        title=plan.title,
                    )
                )
