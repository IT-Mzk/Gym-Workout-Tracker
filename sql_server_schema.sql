CREATE DATABASE GymWorkoutTracker;
GO

USE GymWorkoutTracker;
GO

CREATE TABLE Users (
    UserId INT IDENTITY(1,1) PRIMARY KEY,
    Username NVARCHAR(50) NOT NULL UNIQUE,
    XPPoints INT NOT NULL DEFAULT 0,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE Routines (
    RoutineId INT IDENTITY(1,1) PRIMARY KEY,
    UserId INT NOT NULL,
    Name NVARCHAR(80) NOT NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_Routines_Users
        FOREIGN KEY (UserId) REFERENCES Users(UserId) ON DELETE CASCADE,
    CONSTRAINT UQ_Routines_User_Name UNIQUE (UserId, Name)
);

CREATE TABLE Exercises (
    ExerciseId INT IDENTITY(1,1) PRIMARY KEY,
    RoutineId INT NOT NULL,
    Name NVARCHAR(80) NOT NULL,
    Sets INT NOT NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_Exercises_Routines
        FOREIGN KEY (RoutineId) REFERENCES Routines(RoutineId) ON DELETE CASCADE,
    CONSTRAINT UQ_Exercises_Routine_Name UNIQUE (RoutineId, Name),
    CONSTRAINT CK_Exercises_Sets_Positive CHECK (Sets > 0)
);

CREATE TABLE WorkoutDays (
    UserId INT NOT NULL,
    DayName NVARCHAR(10) NOT NULL,
    CONSTRAINT PK_WorkoutDays PRIMARY KEY (UserId, DayName),
    CONSTRAINT FK_WorkoutDays_Users
        FOREIGN KEY (UserId) REFERENCES Users(UserId) ON DELETE CASCADE,
    CONSTRAINT CK_WorkoutDays_DayName CHECK (
        DayName IN (
            'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY',
            'FRIDAY', 'SATURDAY', 'SUNDAY'
        )
    )
);

CREATE TABLE WorkoutLogs (
    WorkoutLogId INT IDENTITY(1,1) PRIMARY KEY,
    UserId INT NOT NULL,
    RoutineId INT NOT NULL,
    PerformedOn DATE NOT NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_WorkoutLogs_Users
        FOREIGN KEY (UserId) REFERENCES Users(UserId) ON DELETE NO ACTION,
    CONSTRAINT FK_WorkoutLogs_Routines
        FOREIGN KEY (RoutineId) REFERENCES Routines(RoutineId) ON DELETE NO ACTION
);

CREATE TABLE WorkoutLogSets (
    WorkoutLogSetId INT IDENTITY(1,1) PRIMARY KEY,
    WorkoutLogId INT NOT NULL,
    ExerciseId INT NOT NULL,
    SetNumber INT NOT NULL,
    Weight DECIMAL(8,2) NOT NULL,
    CONSTRAINT FK_WorkoutLogSets_WorkoutLogs
        FOREIGN KEY (WorkoutLogId) REFERENCES WorkoutLogs(WorkoutLogId) ON DELETE CASCADE,
    CONSTRAINT FK_WorkoutLogSets_Exercises
        FOREIGN KEY (ExerciseId) REFERENCES Exercises(ExerciseId) ON DELETE NO ACTION,
    CONSTRAINT CK_WorkoutLogSets_SetNumber_Positive CHECK (SetNumber > 0),
    CONSTRAINT CK_WorkoutLogSets_Weight_NonNegative CHECK (Weight >= 0)
);
