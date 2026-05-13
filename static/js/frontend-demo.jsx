const { useDeferredValue, useMemo, useState, useTransition } = React;

const DAY_ORDER = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
];

const TIME_SLOTS = ["06:30", "18:15", "19:00", "07:00", "17:45", "10:00"];

const INITIAL_DATA = {
    user: {
        name: "Mina Carter",
        initials: "MC",
        level: 7,
        xpCurrent: 420,
        xpGoal: 1000,
        streak: 5,
        weeklyGoal: "4 focused sessions",
        focus: "Strength and physique phase",
    },
    workoutDays: ["Monday", "Wednesday", "Friday", "Sunday"],
    routines: [
        {
            id: "upper-power",
            name: "Upper Power",
            focus: "Heavy pressing, rows and pull-ups",
            volume: "14 working sets",
            lastLog: "Apr 11",
            exercises: [
                { name: "Bench Press", sets: 4 },
                { name: "Weighted Pull-Up", sets: 4 },
                { name: "Seated Press", sets: 3 },
                { name: "Cable Row", sets: 3 },
            ],
        },
        {
            id: "lower-strength",
            name: "Lower Strength",
            focus: "Squat, hinge and single-leg work",
            volume: "16 working sets",
            lastLog: "Apr 09",
            exercises: [
                { name: "Back Squat", sets: 4 },
                { name: "Romanian Deadlift", sets: 4 },
                { name: "Walking Lunge", sets: 4 },
                { name: "Leg Curl", sets: 4 },
            ],
        },
        {
            id: "conditioning-core",
            name: "Conditioning Core",
            focus: "Work capacity and trunk stability",
            volume: "10 working sets",
            lastLog: "Apr 07",
            exercises: [
                { name: "Sled Push", sets: 5 },
                { name: "Battle Rope", sets: 3 },
                { name: "Hanging Knee Raise", sets: 2 },
            ],
        },
    ],
    records: [
        { label: "Back Squat", value: "295 lbs" },
        { label: "Bench Press", value: "205 lbs" },
        { label: "Romanian Deadlift", value: "255 lbs" },
        { label: "Weighted Pull-Up", value: "+45 lbs" },
    ],
    history: [
        {
            date: "Apr 11",
            routine: "Upper Power",
            note: "Bench moved faster this week. Pull-ups stayed clean.",
        },
        {
            date: "Apr 09",
            routine: "Lower Strength",
            note: "Squat top sets felt solid. Tempo stayed consistent.",
        },
        {
            date: "Apr 07",
            routine: "Conditioning Core",
            note: "Finished sled circuit ahead of target time.",
        },
    ],
};

function classNames(...parts) {
    return parts.filter(Boolean).join(" ");
}

function initialsFromName(name) {
    const parts = name
        .trim()
        .split(/\s+/)
        .filter(Boolean)
        .slice(0, 2);

    if (!parts.length) {
        return "GT";
    }

    return parts.map((part) => part[0].toUpperCase()).join("");
}

function createId(value, takenIds) {
    const baseId =
        value
            .toLowerCase()
            .trim()
            .replace(/[^a-z0-9]+/g, "-")
            .replace(/^-+|-+$/g, "") || "routine";

    if (!takenIds.has(baseId)) {
        return baseId;
    }

    let suffix = 2;
    while (takenIds.has(`${baseId}-${suffix}`)) {
        suffix += 1;
    }
    return `${baseId}-${suffix}`;
}

function getTodayName() {
    return new Intl.DateTimeFormat("en-US", {
        weekday: "long",
    }).format(new Date());
}

function getNextWorkoutDay(days) {
    if (!days.length) {
        return "No workout day selected";
    }

    const today = getTodayName();
    const todayIndex = DAY_ORDER.indexOf(today);
    const sortedDays = [...days].sort(
        (left, right) => DAY_ORDER.indexOf(left) - DAY_ORDER.indexOf(right),
    );
    const nextDay = sortedDays.find(
        (day) => DAY_ORDER.indexOf(day) >= todayIndex,
    );
    return nextDay ?? sortedDays[0];
}

function buildSessions(days, routines) {
    const today = getTodayName();
    const nextWorkout = getNextWorkoutDay(days);

    return [...days]
        .sort((left, right) => DAY_ORDER.indexOf(left) - DAY_ORDER.indexOf(right))
        .map((day, index) => {
            const routine = routines.length
                ? routines[index % routines.length]
                : null;

            let status = "completed";
            let label = "Completed";
            if (day === today) {
                status = "focus";
                label = "Today";
            } else if (day === nextWorkout) {
                status = "upcoming";
                label = "Next up";
            } else if (DAY_ORDER.indexOf(day) > DAY_ORDER.indexOf(today)) {
                status = "upcoming";
                label = "Upcoming";
            }

            return {
                day,
                time: TIME_SLOTS[index % TIME_SLOTS.length],
                routine: routine ? routine.name : "Open slot",
                focus: routine
                    ? routine.focus
                    : "Shape a routine in Planner to fill this session.",
                status,
                label,
            };
        });
}

function MetricCard({ label, value }) {
    return (
        <article className="metric-card">
            <div className="metric-label">{label}</div>
            <div className="metric-value">{value}</div>
        </article>
    );
}

function SectionHeader({ eyebrow, title, copy, actions }) {
    return (
        <div className="section-head">
            <div>
                <p className="eyebrow">{eyebrow}</p>
                <h2 className="section-title">{title}</h2>
                {copy ? <p className="section-copy">{copy}</p> : null}
            </div>
            {actions}
        </div>
    );
}

function LoginView({
    loginName,
    setLoginName,
    onLogin,
    onQuickDemo,
}) {
    return (
        <main className="login-demo-page">
            <div className="login-demo-shell">
                <section className="login-demo-copy">
                    <div className="brand-row">
                        <div className="brand-mark">GT</div>
                        <div className="brand-copy">
                            <strong>Gym Tracker</strong>
                            <span>Frontend-only demo</span>
                        </div>
                    </div>

                    <p className="eyebrow">Pre-login mock</p>
                    <h1 className="hero-title">
                        A cleaner first screen before the athlete enters the dashboard.
                    </h1>
                    <p className="hero-copy">
                        This login is only part of the demo flow. It does not call
                        any backend, but it helps us design the experience before
                        the user reaches planning, schedule and profile screens.
                    </p>

                    <div className="login-feature-grid">
                        <article className="login-feature-card">
                            <strong>Fast access</strong>
                            <span>One field keeps the flow lightweight and friendly.</span>
                        </article>
                        <article className="login-feature-card">
                            <strong>Consistent tone</strong>
                            <span>The first screen matches the same athletic visual system.</span>
                        </article>
                        <article className="login-feature-card">
                            <strong>Demo ready</strong>
                            <span>You can enter any name or jump in with a demo athlete.</span>
                        </article>
                    </div>
                </section>

                <section className="login-demo-panel">
                    <p className="eyebrow">Sign in</p>
                    <h2 className="section-title">Enter your training space</h2>
                    <p className="section-copy">
                        Type a name to simulate login and open the frontend demo.
                    </p>

                    <form className="composer-form" onSubmit={onLogin}>
                        <div className="field-group">
                            <label htmlFor="loginName">Athlete name</label>
                            <input
                                id="loginName"
                                value={loginName}
                                onChange={(event) => setLoginName(event.target.value)}
                                placeholder="Example: Mina Carter"
                            />
                        </div>

                        <button className="button" type="submit">
                            Open demo dashboard
                        </button>
                    </form>

                    <div className="button-row">
                        <button
                            className="ghost-button"
                            onClick={onQuickDemo}
                            type="button"
                        >
                            Continue as demo athlete
                        </button>
                    </div>

                    <div className="login-demo-note">
                        This is a UI mock. Refreshing the page or logging out will
                        return you to this form.
                    </div>
                </section>
            </div>
        </main>
    );
}

function DashboardView(props) {
    const {
        routines,
        workoutDays,
        totalExercises,
        nextWorkout,
        activeRoutineId,
        setActiveRoutineId,
        onJump,
    } = props;

    const featuredRoutine =
        routines.find((routine) => routine.id === activeRoutineId) ??
        routines[0] ??
        null;

    return (
        <>
            <section className="hero-grid">
                <article className="hero-card">
                    <p className="eyebrow">Frontend prototype</p>
                    <h1 className="hero-title">
                        A clearer training dashboard for routines, logs and
                        progress.
                    </h1>
                    <p className="hero-copy">
                        This UI is powered only by mocked React state so we can
                        shape the frontend direction before touching backend
                        work.
                    </p>
                    <div className="button-row">
                        <button className="button" onClick={() => onJump("plan")} type="button">
                            Open planner
                        </button>
                        <button className="ghost-button" onClick={() => onJump("schedule")} type="button">
                            Review schedule
                        </button>
                    </div>
                </article>

                <div className="metric-grid">
                    <MetricCard label="Routines" value={routines.length} />
                    <MetricCard label="Exercises" value={totalExercises} />
                    <MetricCard label="Workout days" value={workoutDays.length} />
                    <MetricCard label="Next workout" value={nextWorkout} />
                </div>
            </section>

            <section className="content-grid">
                <article className="glass-card">
                    <SectionHeader
                        eyebrow="Routine library"
                        title="Choose the block you want to focus on"
                        copy="These cards are designed as the visual home for routine management."
                    />

                    <div className="routine-grid">
                        {routines.map((routine) => (
                            <button
                                key={routine.id}
                                className={classNames(
                                    "routine-card",
                                    routine.id === activeRoutineId && "is-active",
                                )}
                                onClick={() => setActiveRoutineId(routine.id)}
                                type="button"
                            >
                                <span className="pill">Routine</span>
                                <h3 className="card-title">{routine.name}</h3>
                                <p className="small-copy">{routine.focus}</p>
                                <ul className="routine-list">
                                    {routine.exercises.map((exercise) => (
                                        <li key={`${routine.id}-${exercise.name}`}>
                                            <span>{exercise.name}</span>
                                            <span>{exercise.sets} sets</span>
                                        </li>
                                    ))}
                                </ul>
                            </button>
                        ))}
                    </div>
                </article>

                <div className="stack">
                    <article className="glass-card">
                        <SectionHeader
                            eyebrow="Quick glance"
                            title={featuredRoutine ? featuredRoutine.name : "No routine selected"}
                            copy="A small detail block for the currently highlighted routine."
                        />
                        {featuredRoutine ? (
                            <ul className="detail-list">
                                <li>
                                    <span>Focus</span>
                                    <span>{featuredRoutine.focus}</span>
                                </li>
                                <li>
                                    <span>Volume</span>
                                    <span>{featuredRoutine.volume}</span>
                                </li>
                                <li>
                                    <span>Last log</span>
                                    <span>{featuredRoutine.lastLog}</span>
                                </li>
                            </ul>
                        ) : (
                            <p className="small-copy">
                                Add a routine in Planner to populate this area.
                            </p>
                        )}
                    </article>

                    <article className="glass-card">
                        <SectionHeader
                            eyebrow="Next steps"
                            title="What this demo is exploring"
                            copy="Card hierarchy, cleaner navigation and a more athletic visual identity."
                        />
                        <div className="quick-grid">
                            <MetricCard label="Primary flow" value="Plan to Log" />
                            <MetricCard label="Mode" value="Mock only" />
                        </div>
                    </article>
                </div>
            </section>
        </>
    );
}

function PlannerView(props) {
    const {
        routines,
        totalExercises,
        routineName,
        setRoutineName,
        routineFocus,
        setRoutineFocus,
        anchorExercise,
        setAnchorExercise,
        onCreateRoutine,
        previewName,
    } = props;

    return (
        <>
            <section className="hero-grid">
                <article className="hero-card">
                    <p className="eyebrow">Planner</p>
                    <h1 className="hero-title">
                        Build routines like strong content blocks.
                    </h1>
                    <p className="hero-copy">
                        This combines overview cards and a creator panel so the
                        planning flow feels closer to a product than a form
                        dump.
                    </p>
                </article>

                <div className="metric-grid">
                    <MetricCard label="Total routines" value={routines.length} />
                    <MetricCard label="Tracked lifts" value={totalExercises} />
                    <MetricCard label="New draft" value={previewName || "Not named yet"} />
                    <MetricCard label="Mode" value="Frontend only" />
                </div>
            </section>

            <section className="content-grid">
                <article className="glass-card">
                    <SectionHeader
                        eyebrow="Routine cards"
                        title="Current split"
                        copy="These cards are intentionally visual and easy to scan."
                    />
                    <div className="routine-grid">
                        {routines.map((routine) => (
                            <article className="routine-card" key={routine.id}>
                                <span className="pill">Live draft</span>
                                <h3 className="card-title">{routine.name}</h3>
                                <p className="small-copy">{routine.focus}</p>
                                <ul className="routine-list">
                                    <li>
                                        <span>Volume</span>
                                        <span>{routine.volume}</span>
                                    </li>
                                    <li>
                                        <span>Exercises</span>
                                        <span>{routine.exercises.length}</span>
                                    </li>
                                    <li>
                                        <span>Last log</span>
                                        <span>{routine.lastLog}</span>
                                    </li>
                                </ul>
                            </article>
                        ))}
                    </div>
                </article>

                <article className="composer-card">
                    <SectionHeader
                        eyebrow="Composer"
                        title="Draft a new routine"
                        copy="This only updates local React state and resets on refresh."
                    />

                    <form className="composer-form" onSubmit={onCreateRoutine}>
                        <div className="field-group">
                            <label htmlFor="routineName">Routine name</label>
                            <input
                                id="routineName"
                                value={routineName}
                                onChange={(event) => setRoutineName(event.target.value)}
                                placeholder="Example: Pull Hypertrophy"
                            />
                        </div>

                        <div className="field-group">
                            <label htmlFor="routineFocus">Focus</label>
                            <input
                                id="routineFocus"
                                value={routineFocus}
                                onChange={(event) => setRoutineFocus(event.target.value)}
                                placeholder="Example: Upper back and biceps volume"
                            />
                        </div>

                        <div className="field-group">
                            <label htmlFor="anchorExercise">Anchor exercise</label>
                            <input
                                id="anchorExercise"
                                value={anchorExercise}
                                onChange={(event) => setAnchorExercise(event.target.value)}
                                placeholder="Example: Barbell Row"
                            />
                        </div>

                        <button className="button" type="submit">
                            Add routine to demo
                        </button>
                    </form>

                    <ul className="detail-list">
                        <li>
                            <span>Preview title</span>
                            <span>{previewName || "New routine"}</span>
                        </li>
                        <li>
                            <span>Focus</span>
                            <span>{routineFocus || "Choose a training goal"}</span>
                        </li>
                        <li>
                            <span>Anchor lift</span>
                            <span>{anchorExercise || "Choose a lead exercise"}</span>
                        </li>
                    </ul>
                </article>
            </section>
        </>
    );
}

function ScheduleView({ workoutDays, toggleDay, sessions, nextWorkout }) {
    return (
        <>
            <section className="hero-grid">
                <article className="hero-card">
                    <p className="eyebrow">Weekly schedule</p>
                    <h1 className="hero-title">
                        Turn the week into a clean training board.
                    </h1>
                    <p className="hero-copy">
                        This stays fully mocked, but it demonstrates how
                        workout-day selection and session cards could feel.
                    </p>
                </article>

                <div className="metric-grid">
                    <MetricCard label="Selected days" value={workoutDays.length} />
                    <MetricCard label="Next workout" value={nextWorkout} />
                    <MetricCard label="Today" value={getTodayName()} />
                    <MetricCard label="Flow" value="Select and Review" />
                </div>
            </section>

            <section className="content-grid">
                <article className="glass-card">
                    <SectionHeader
                        eyebrow="Day selector"
                        title="Choose your workout days"
                        copy="Each toggle updates only local demo state."
                    />

                    <div className="day-grid">
                        {DAY_ORDER.map((day) => (
                            <button
                                key={day}
                                type="button"
                                className={classNames(
                                    "day-pill",
                                    workoutDays.includes(day) && "is-selected",
                                )}
                                onClick={() => toggleDay(day)}
                            >
                                <strong>{day}</strong>
                                <span className="small-copy">
                                    {workoutDays.includes(day)
                                        ? "Scheduled session"
                                        : "Rest or available"}
                                </span>
                            </button>
                        ))}
                    </div>
                </article>

                <article className="glass-card">
                    <SectionHeader
                        eyebrow="Session flow"
                        title="Upcoming sessions"
                        copy="A preview of how the eventual logging flow could branch off each workout day."
                    />

                    <div className="stack">
                        {sessions.length ? (
                            sessions.map((session) => (
                                <article className="timeline-card" key={session.day}>
                                    <div className="status-row">
                                        <strong className="card-title">{session.day}</strong>
                                        <span className={classNames("status-tag", session.status)}>
                                            {session.label}
                                        </span>
                                    </div>
                                    <div className="small-copy">
                                        {session.time} - {session.routine}
                                    </div>
                                    <div>{session.focus}</div>
                                </article>
                            ))
                        ) : (
                            <p className="small-copy">
                                No workout days selected yet. Toggle a day to
                                generate live session cards in the demo.
                            </p>
                        )}
                    </div>
                </article>
            </section>
        </>
    );
}

function ProfileView({ user, records, history, totalExercises, nextWorkout }) {
    return (
        <>
            <section className="hero-grid">
                <article className="hero-card">
                    <p className="eyebrow">Profile</p>
                    <h1 className="hero-title">
                        A progress page that feels motivating instead of flat.
                    </h1>
                    <p className="hero-copy">
                        The goal here is a stronger sense of identity with richer
                        cards, clearer type and better spacing.
                    </p>
                </article>

                <article className="profile-card">
                    <div className="user-top">
                        <div className="user-avatar">{user.initials}</div>
                        <div className="user-meta">
                            <strong className="profile-name">{user.name}</strong>
                            <span>Level {user.level} athlete</span>
                            <span>{user.focus}</span>
                        </div>
                    </div>

                    <div className="progress-shell">
                        <div className="progress-meta">
                            <span>XP progress</span>
                            <span>{user.xpCurrent}/{user.xpGoal}</span>
                        </div>
                        <div className="progress-bar">
                            <span
                                style={{
                                    width: `${(user.xpCurrent / user.xpGoal) * 100}%`,
                                }}
                            />
                        </div>
                    </div>
                </article>
            </section>

            <section className="content-grid">
                <article className="glass-card">
                    <SectionHeader
                        eyebrow="Records"
                        title="Personal record snapshot"
                        copy="These cards are mock data, but the layout is ready for real progress later."
                    />
                    <div className="profile-grid">
                        {records.map((record) => (
                            <article className="metric-card" key={record.label}>
                                <div className="metric-label">{record.label}</div>
                                <div className="metric-value">{record.value}</div>
                            </article>
                        ))}
                    </div>
                </article>

                <div className="stack">
                    <article className="glass-card">
                        <SectionHeader
                            eyebrow="Highlights"
                            title="Current focus"
                            copy="Compact highlight cards help the profile read as a dashboard."
                        />
                        <div className="quick-grid">
                            <MetricCard label="Streak" value={`${user.streak} days`} />
                            <MetricCard label="Next workout" value={nextWorkout} />
                            <MetricCard label="Tracked lifts" value={totalExercises} />
                            <MetricCard label="Weekly goal" value={user.weeklyGoal} />
                        </div>
                    </article>
                </div>
            </section>

            <section className="table-card">
                <SectionHeader
                    eyebrow="Recent history"
                    title="Latest training notes"
                    copy="This section shows how a lightweight history table could fit into the final UI."
                />
                <div className="table-shell">
                    <table>
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Routine</th>
                                <th>Notes</th>
                            </tr>
                        </thead>
                        <tbody>
                            {history.map((entry) => (
                                <tr key={`${entry.date}-${entry.routine}`}>
                                    <td>{entry.date}</td>
                                    <td>{entry.routine}</td>
                                    <td>{entry.note}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </section>
        </>
    );
}

function App() {
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [loginName, setLoginName] = useState("");
    const [activeView, setActiveView] = useState("dashboard");
    const [data, setData] = useState(INITIAL_DATA);
    const [activeRoutineId, setActiveRoutineId] = useState(
        INITIAL_DATA.routines[0].id,
    );
    const [routineName, setRoutineName] = useState("");
    const [routineFocus, setRoutineFocus] = useState("");
    const [anchorExercise, setAnchorExercise] = useState("");
    const [isPending, startTransition] = useTransition();
    const deferredRoutineName = useDeferredValue(routineName);

    const totalExercises = useMemo(
        () =>
            data.routines.reduce(
                (sum, routine) => sum + routine.exercises.length,
                0,
            ),
        [data.routines],
    );

    const nextWorkout = useMemo(
        () => getNextWorkoutDay(data.workoutDays),
        [data.workoutDays],
    );

    const sessions = useMemo(
        () => buildSessions(data.workoutDays, data.routines),
        [data.workoutDays, data.routines],
    );

    const navItems = [
        { id: "dashboard", label: "Dashboard" },
        { id: "plan", label: "Planner" },
        { id: "schedule", label: "Schedule" },
        { id: "profile", label: "Profile" },
    ];

    function jumpTo(viewId) {
        startTransition(() => {
            setActiveView(viewId);
        });
    }

    function enterDemo(name) {
        const trimmedName = name.trim();
        const athleteName = trimmedName || INITIAL_DATA.user.name;

        startTransition(() => {
            setData((current) => ({
                ...current,
                user: {
                    ...current.user,
                    name: athleteName,
                    initials: initialsFromName(athleteName),
                    focus: trimmedName
                        ? "Custom athlete demo profile"
                        : INITIAL_DATA.user.focus,
                },
            }));
            setActiveView("dashboard");
            setIsLoggedIn(true);
        });
    }

    function handleLogin(event) {
        event.preventDefault();
        enterDemo(loginName);
    }

    function handleQuickDemo() {
        setLoginName(INITIAL_DATA.user.name);
        enterDemo(INITIAL_DATA.user.name);
    }

    function handleLogout() {
        startTransition(() => {
            setData(INITIAL_DATA);
            setActiveRoutineId(INITIAL_DATA.routines[0].id);
            setActiveView("dashboard");
            setIsLoggedIn(false);
        });
        setLoginName("");
        setRoutineName("");
        setRoutineFocus("");
        setAnchorExercise("");
    }

    function resetDemo() {
        startTransition(() => {
            setData(INITIAL_DATA);
            setActiveRoutineId(INITIAL_DATA.routines[0].id);
            setActiveView("dashboard");
        });
        setRoutineName("");
        setRoutineFocus("");
        setAnchorExercise("");
    }

    function toggleDay(day) {
        startTransition(() => {
            setData((current) => {
                const nextDays = current.workoutDays.includes(day)
                    ? current.workoutDays.filter((item) => item !== day)
                    : [...current.workoutDays, day];

                return {
                    ...current,
                    workoutDays: nextDays,
                };
            });
        });
    }

    function handleCreateRoutine(event) {
        event.preventDefault();
        const trimmedName = routineName.trim();
        if (!trimmedName) {
            return;
        }

        const takenIds = new Set(data.routines.map((routine) => routine.id));
        const nextRoutine = {
            id: createId(trimmedName, takenIds),
            name: trimmedName,
            focus: routineFocus.trim() || "Custom training block",
            volume: "12 working sets",
            lastLog: "New draft",
            exercises: [
                { name: anchorExercise.trim() || "Primary Lift", sets: 4 },
                { name: "Secondary Lift", sets: 3 },
                { name: "Accessory Finisher", sets: 3 },
            ],
        };

        startTransition(() => {
            setData((current) => ({
                ...current,
                routines: [nextRoutine, ...current.routines],
            }));
            setActiveRoutineId(nextRoutine.id);
            setActiveView("plan");
        });

        setRoutineName("");
        setRoutineFocus("");
        setAnchorExercise("");
    }

    let view = null;

    if (activeView === "dashboard") {
        view = (
            <DashboardView
                routines={data.routines}
                workoutDays={data.workoutDays}
                totalExercises={totalExercises}
                nextWorkout={nextWorkout}
                activeRoutineId={activeRoutineId}
                setActiveRoutineId={setActiveRoutineId}
                onJump={jumpTo}
            />
        );
    }

    if (activeView === "plan") {
        view = (
            <PlannerView
                routines={data.routines}
                totalExercises={totalExercises}
                routineName={routineName}
                setRoutineName={setRoutineName}
                routineFocus={routineFocus}
                setRoutineFocus={setRoutineFocus}
                anchorExercise={anchorExercise}
                setAnchorExercise={setAnchorExercise}
                onCreateRoutine={handleCreateRoutine}
                previewName={deferredRoutineName}
            />
        );
    }

    if (activeView === "schedule") {
        view = (
            <ScheduleView
                workoutDays={data.workoutDays}
                toggleDay={toggleDay}
                sessions={sessions}
                nextWorkout={nextWorkout}
            />
        );
    }

    if (activeView === "profile") {
        view = (
            <ProfileView
                user={data.user}
                records={data.records}
                history={data.history}
                totalExercises={totalExercises}
                nextWorkout={nextWorkout}
            />
        );
    }

    if (!isLoggedIn) {
        return (
            <LoginView
                loginName={loginName}
                setLoginName={setLoginName}
                onLogin={handleLogin}
                onQuickDemo={handleQuickDemo}
            />
        );
    }

    return (
        <div className="demo-app">
            <aside className="demo-sidebar">
                <div className="brand-row">
                    <div className="brand-mark">GT</div>
                    <div className="brand-copy">
                        <strong>Gym Tracker</strong>
                        <span>React frontend demo</span>
                    </div>
                </div>

                <div className="user-panel">
                    <div className="user-top">
                        <div className="user-avatar">{data.user.initials}</div>
                        <div className="user-meta">
                            <strong>{data.user.name}</strong>
                            <span>Level {data.user.level}</span>
                            <span>{data.user.weeklyGoal}</span>
                        </div>
                    </div>

                    <div className="progress-shell">
                        <div className="progress-meta">
                            <span>XP</span>
                            <span>{data.user.xpCurrent}/{data.user.xpGoal}</span>
                        </div>
                        <div className="progress-bar">
                            <span
                                style={{
                                    width: `${(data.user.xpCurrent / data.user.xpGoal) * 100}%`,
                                }}
                            />
                        </div>
                    </div>
                </div>

                <div className="sidebar-block">
                    <p className="eyebrow">Navigation</p>
                    <div className="nav-list">
                        {navItems.map((item) => (
                            <button
                                key={item.id}
                                className={classNames(
                                    "nav-button",
                                    activeView === item.id && "is-active",
                                    isPending && "is-pending",
                                )}
                                onClick={() => jumpTo(item.id)}
                                type="button"
                            >
                                {item.label}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="sidebar-block">
                    <p className="eyebrow">Demo stats</p>
                    <div className="sidebar-stats">
                        <div className="sidebar-stat">
                            <strong>{data.routines.length}</strong>
                            <span>Routines</span>
                        </div>
                        <div className="sidebar-stat">
                            <strong>{data.workoutDays.length}</strong>
                            <span>Workout days</span>
                        </div>
                        <div className="sidebar-stat">
                            <strong>{totalExercises}</strong>
                            <span>Exercises</span>
                        </div>
                        <div className="sidebar-stat">
                            <strong>{nextWorkout}</strong>
                            <span>Next up</span>
                        </div>
                    </div>
                </div>
            </aside>

            <main className="demo-main">
                <div className="top-note">
                    <div>
                        <strong>Frontend-only demo.</strong> All data on this
                        page is mocked inside React and resets on refresh. No
                        API calls and no backend persistence are involved.
                    </div>
                    <div className="button-row top-note-actions">
                        <button className="ghost-button" onClick={resetDemo} type="button">
                            Reset demo
                        </button>
                        <button className="ghost-button" onClick={handleLogout} type="button">
                            Log out
                        </button>
                    </div>
                </div>

                {view}
            </main>
        </div>
    );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
