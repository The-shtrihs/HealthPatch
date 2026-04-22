from src.activity.domain.models import (
    ExerciseDomain,
    ExerciseSessionDomain,
    MuscleGroupDomain,
    PersonalRecordDomain,
    PlanTrainingDomain,
    PlanTrainingExerciseDomain,
    RepCount,
    SetNumber,
    TimeRange,
    WeightKg,
    WorkoutPlanDomain,
    WorkoutSessionDomain,
    WorkoutSetDomain,
)
from src.activity.domain.models import (
    Weekday as DomainWeekday,
)
from src.models.activity import (
    Exercise,
    ExerciseMuscleGroup,
    ExerciseSession,
    MuscleGroup,
    PersonalRecord,
    PlanTraining,
    PlanTrainingExercise,
    WorkoutPlan,
    WorkoutSession,
    WorkoutSet,
)
from src.models.activity import (
    Weekday as OrmWeekday,
)


def muscle_group_to_domain(orm: MuscleGroup) -> MuscleGroupDomain:
    return MuscleGroupDomain(id=orm.id, name=orm.name)


def exercise_to_domain(orm: Exercise) -> ExerciseDomain:
    primary = muscle_group_to_domain(orm.primary_muscle_group) if orm.primary_muscle_group else None
    secondary: list[MuscleGroupDomain] = []
    links = orm.secondary_muscle_group_links or []
    for link in links:
        if isinstance(link, ExerciseMuscleGroup) and link.muscle_group is not None:
            secondary.append(muscle_group_to_domain(link.muscle_group))
    return ExerciseDomain(
        id=orm.id,
        name=orm.name,
        primary_muscle_group=primary,
        secondary_muscle_groups=secondary,
    )


def plan_training_exercise_to_domain(orm: PlanTrainingExercise) -> PlanTrainingExerciseDomain:
    exercise_name = orm.exercise.name if orm.exercise is not None else None
    return PlanTrainingExerciseDomain(
        id=orm.id,
        plan_training_id=orm.plan_training_id,
        exercise_id=orm.exercise_id,
        exercise_name=exercise_name,
        order_num=orm.order_num,
        target_sets=orm.target_sets,
        target_reps=orm.target_reps,
        target_weight_pct=orm.target_weight_pct,
    )


def plan_training_to_domain(orm: PlanTraining, include_exercises: bool = True) -> PlanTrainingDomain:
    exercises: list[PlanTrainingExerciseDomain] = []
    if include_exercises:
        exercises = [plan_training_exercise_to_domain(pte) for pte in sorted(orm.exercises or [], key=lambda x: x.order_num)]
    weekday = DomainWeekday(orm.weekday.value) if orm.weekday is not None else None
    return PlanTrainingDomain(
        id=orm.id,
        plan_id=orm.plan_id,
        name=orm.name,
        weekday=weekday,
        order_num=orm.order_num,
        exercises=exercises,
    )


def workout_plan_to_domain(orm: WorkoutPlan, include_trainings: bool = False) -> WorkoutPlanDomain:
    trainings: list[PlanTrainingDomain] = []
    if include_trainings:
        trainings = [plan_training_to_domain(t) for t in sorted(orm.trainings or [], key=lambda x: x.order_num)]
    return WorkoutPlanDomain(
        id=orm.id,
        author_id=orm.author_id,
        title=orm.title,
        description=orm.description,
        is_public=orm.is_public,
        trainings=trainings,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )


def workout_set_to_domain(orm: WorkoutSet) -> WorkoutSetDomain:
    return WorkoutSetDomain(
        id=orm.id,
        exercise_session_id=orm.exercise_session_id,
        set_number=SetNumber(orm.set_number),
        reps=RepCount(orm.reps),
        weight=WeightKg(orm.weight),
    )


def exercise_session_to_domain(orm: ExerciseSession, include_sets: bool = True) -> ExerciseSessionDomain:
    try:
        exercise_name = orm.exercise.name if orm.exercise is not None else None
    except Exception:
        exercise_name = None
    sets: list[WorkoutSetDomain] = []
    if include_sets:
        try:
            sets = [workout_set_to_domain(s) for s in (orm.sets or [])]
        except Exception:
            sets = []
    return ExerciseSessionDomain(
        id=orm.id,
        workout_session_id=orm.workout_session_id,
        exercise_id=orm.exercise_id,
        exercise_name=exercise_name,
        order_num=orm.order_num,
        is_from_template=orm.is_from_template,
        sets=sets,
    )


def workout_session_to_domain(orm: WorkoutSession, include_children: bool = False) -> WorkoutSessionDomain:
    children: list[ExerciseSessionDomain] = []
    if include_children:
        children = [exercise_session_to_domain(es) for es in sorted(orm.exercise_sessions or [], key=lambda x: x.order_num)]
    return WorkoutSessionDomain(
        id=orm.id,
        user_id=orm.user_id,
        plan_training_id=orm.plan_training_id,
        time_range=TimeRange(started_at=orm.started_at, ended_at=orm.ended_at),
        exercise_sessions=children,
    )


def personal_record_to_domain(orm: PersonalRecord) -> PersonalRecordDomain:
    exercise_name = orm.exercise.name if getattr(orm, "exercise", None) is not None else None
    return PersonalRecordDomain(
        id=orm.id,
        user_id=orm.user_id,
        exercise_id=orm.exercise_id,
        exercise_name=exercise_name,
        weight=WeightKg(orm.weight),
        recorded_at=orm.recorded_at,
    )


def domain_weekday_to_orm(weekday: DomainWeekday | None) -> OrmWeekday | None:
    return OrmWeekday(weekday.value) if weekday is not None else None


def apply_domain_to_workout_plan_orm(domain: WorkoutPlanDomain, orm: WorkoutPlan) -> None:
    orm.title = domain.title
    orm.description = domain.description
    orm.is_public = domain.is_public


def apply_domain_to_workout_session_orm(domain: WorkoutSessionDomain, orm: WorkoutSession) -> None:
    orm.ended_at = domain.ended_at
