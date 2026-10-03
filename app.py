from flask import Flask, render_template, jsonify, request
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
EXCEL_FILE = BASE_DIR / "data" / "attendance.xlsx"


# =========================================================
# LOAD EXCEL DATA
# =========================================================

def load_data():

    if not EXCEL_FILE.exists():
        return pd.DataFrame(
            columns=["Date", "Day", "Roll_No", "Status"]
        )

    df = pd.read_excel(
        EXCEL_FILE,
        sheet_name="Attendance_Data"
    )

    df.columns = df.columns.astype(str).str.strip()

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce"
    )

    df["Roll_No"] = (
        df["Roll_No"]
        .astype(str)
        .str.strip()
    )

    df["Status"] = (
        df["Status"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    df["Status"] = df["Status"].replace({
        "PRESENT": "P",
        "ABSENT": "A"
    })

    df = df.dropna(
        subset=["Date", "Roll_No"]
    )

    df = df[
        df["Status"].isin(["P", "A"])
    ]

    df = df.sort_values(
        ["Date", "Roll_No"]
    )

    return df


df = load_data()


# =========================================================
# FEATURE ENGINEERING
# =========================================================

def create_features(history):

    values = (
        history["Status"]
        .map({"P": 1, "A": 0})
        .to_numpy()
    )

    total = len(values)

    def percentage(n):

        if total == 0:
            return 0

        return float(
            values[-n:].mean() * 100
        )

    attendance_percentage = (
        values.mean() * 100
        if total else 0
    )

    last_3 = percentage(3)
    last_5 = percentage(5)
    last_10 = percentage(10)
    last_20 = percentage(20)

    consecutive_absent = 0

    for value in values[::-1]:

        if value == 0:
            consecutive_absent += 1

        else:
            break

    consecutive_present = 0

    for value in values[::-1]:

        if value == 1:
            consecutive_present += 1

        else:
            break

    half = max(
        1,
        min(10, total // 2)
    )

    if total >= half * 2:

        recent_average = values[-half:].mean()
        previous_average = values[-2 * half:-half].mean()

        trend = (
            recent_average -
            previous_average
        ) * 100

    else:

        trend = 0

    return [
        attendance_percentage,
        last_3,
        last_5,
        last_10,
        last_20,
        consecutive_absent,
        consecutive_present,
        trend
    ]


# =========================================================
# TRAIN ML MODEL
# =========================================================

def train_model():

    X = []
    y = []

    for roll_no in df["Roll_No"].unique():

        student = df[
            df["Roll_No"] == roll_no
        ].sort_values("Date")

        for i in range(5, len(student)):

            history = student.iloc[:i]

            X.append(
                create_features(history)
            )

            y.append(
                1
                if student.iloc[i]["Status"] == "P"
                else 0
            )

    if len(set(y)) < 2:
        return None

    model = RandomForestClassifier(
        n_estimators=250,
        max_depth=12,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42
    )

    model.fit(X, y)

    return model


model = train_model()


# =========================================================
# STUDENT STATISTICS
# =========================================================

def get_student_stats(roll_no):

    student = df[
        df["Roll_No"] == str(roll_no)
    ].sort_values("Date")

    if student.empty:
        return None

    total = len(student)

    present = int(
        (student["Status"] == "P").sum()
    )

    absent = total - present

    percentage = (
        present / total * 100
        if total
        else 0
    )

    last_5 = (
        (student.tail(5)["Status"] == "P")
        .mean() * 100
    )

    last_10 = (
        (student.tail(10)["Status"] == "P")
        .mean() * 100
    )

    return {
        "roll_no": str(roll_no),
        "classes": total,
        "present": present,
        "absent": absent,
        "percentage": round(
            percentage,
            2
        ),
        "last_5": round(
            last_5,
            2
        ),
        "last_10": round(
            last_10,
            2
        ),
        "last_status": student.iloc[-1]["Status"],
        "first_date": student.iloc[0]["Date"].strftime(
            "%Y-%m-%d"
        ),
        "last_date": student.iloc[-1]["Date"].strftime(
            "%Y-%m-%d"
        )
    }


# =========================================================
# FUTURE PREDICTION
# =========================================================

def predict_student(
    roll_no,
    target_date
):

    student = df[
        df["Roll_No"] == str(roll_no)
    ].sort_values("Date")

    if student.empty:
        return None

    target_date = pd.Timestamp(
        target_date
    )

    # Check actual attendance first
    actual = student[
        student["Date"] == target_date
    ]

    if not actual.empty:

        status = actual.iloc[0]["Status"]

        return {
            "date": target_date.strftime(
                "%Y-%m-%d"
            ),
            "status": status,
            "prob_present": (
                100 if status == "P" else 0
            ),
            "prob_absent": (
                0 if status == "P" else 100
            ),
            "actual": True
        }

    history = student[
        student["Date"] < target_date
    ]

    if history.empty:
        return None

    features = np.array(
        create_features(history)
    ).reshape(1, -1)

    if model:

        probabilities = (
            model.predict_proba(features)[0]
        )

        classes = list(
            model.classes_
        )

        if 1 in classes:
            present_probability = (
                probabilities[
                    classes.index(1)
                ] * 100
            )
        else:
            present_probability = 0

        if 0 in classes:
            absent_probability = (
                probabilities[
                    classes.index(0)
                ] * 100
            )
        else:
            absent_probability = 0

    else:

        present_probability = (
            history["Status"] == "P"
        ).mean() * 100

        absent_probability = (
            100 - present_probability
        )

    status = (
        "P"
        if present_probability >= absent_probability
        else "A"
    )

    return {
        "date": target_date.strftime(
            "%Y-%m-%d"
        ),
        "status": status,
        "prob_present": round(
            present_probability,
            2
        ),
        "prob_absent": round(
            absent_probability,
            2
        ),
        "actual": False
    }


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# SUMMARY API
# =========================================================

@app.route("/api/summary")
def summary():

    total_records = len(df)

    present = int(
        (df["Status"] == "P").sum()
    )

    absent = (
        total_records - present
    )

    attendance = (
        present / total_records * 100
        if total_records
        else 0
    )

    return jsonify({

        "students": int(
            df["Roll_No"].nunique()
        ),

        "classes": int(
            df["Date"].nunique()
        ),

        "records": total_records,

        "present": present,

        "absent": absent,

        "attendance": round(
            attendance,
            2
        )
    })


# =========================================================
# STUDENTS API
# =========================================================

@app.route("/api/students")
def students():

    search = request.args.get(
        "q",
        ""
    ).lower().strip()

    result = []

    for roll_no in sorted(
        df["Roll_No"].unique()
    ):

        if search and search not in str(
            roll_no
        ).lower():

            continue

        stats = get_student_stats(
            roll_no
        )

        if stats:
            result.append(stats)

    return jsonify(result)


# =========================================================
# SINGLE STUDENT API
# =========================================================

@app.route("/api/student/<roll_no>")
def student_details(roll_no):

    stats = get_student_stats(
        roll_no
    )

    if not stats:

        return jsonify({
            "error": "Student not found"
        }), 404

    student = df[
        df["Roll_No"] == str(roll_no)
    ].sort_values("Date")

    history = []

    for _, row in student.iterrows():

        history.append({

            "date": row["Date"].strftime(
                "%Y-%m-%d"
            ),

            "day": row["Date"].strftime(
                "%A"
            ),

            "status": row["Status"]
        })

    stats["history"] = history

    return jsonify(stats)


# =========================================================
# DAILY ANALYTICS
# =========================================================

@app.route("/api/daily")
def daily():

    result = (
        df.groupby("Date")
        .Status
        .agg(
            classes="count",
            present=lambda x:
                int((x == "P").sum())
        )
        .reset_index()
    )

    result["absent"] = (
        result["classes"]
        - result["present"]
    )

    result["attendance"] = (
        result["present"]
        / result["classes"]
        * 100
    ).round(2)

    result["date"] = (
        result["Date"]
        .dt.strftime("%Y-%m-%d")
    )

    return jsonify(
        result[
            [
                "date",
                "classes",
                "present",
                "absent",
                "attendance"
            ]
        ].to_dict("records")
    )


# =========================================================
# MONTHLY ANALYTICS
# =========================================================

@app.route("/api/monthly")
def monthly():

    result = (
        df.assign(
            month=df["Date"]
            .dt.strftime("%Y-%m")
        )
        .groupby("month")
        .Status
        .agg(
            classes="count",
            present=lambda x:
                int((x == "P").sum())
        )
        .reset_index()
    )

    result["absent"] = (
        result["classes"]
        - result["present"]
    )

    result["attendance"] = (
        result["present"]
        / result["classes"]
        * 100
    ).round(2)

    return jsonify(
        result.to_dict(
            "records"
        )
    )


# =========================================================
# PREDICT ONE DATE
# =========================================================

@app.route("/api/predict")
def predict():

    roll_no = request.args.get(
        "roll_no"
    )

    date = request.args.get(
        "date"
    )

    if not roll_no or not date:

        return jsonify({
            "error":
            "roll_no and date are required"
        }), 400

    result = predict_student(
        roll_no,
        date
    )

    if not result:

        return jsonify({
            "error":
            "Student or date unavailable"
        }), 404

    return jsonify(result)


# =========================================================
# FUTURE FORECAST
# =========================================================

@app.route("/api/future")
def future():

    roll_no = request.args.get(
        "roll_no"
    )

    days = int(
        request.args.get(
            "days",
            7
        )
    )

    days = max(
        1,
        min(days, 60)
    )

    student = df[
        df["Roll_No"] == str(roll_no)
    ]

    if student.empty:

        return jsonify({
            "error":
            "Student not found"
        }), 404

    last_date = student["Date"].max()

    results = []

    for i in range(
        1,
        days + 1
    ):

        target = (
            last_date
            + pd.Timedelta(days=i)
        )

        result = predict_student(
            roll_no,
            target
        )

        results.append(result)

    return jsonify(results)


# =========================================================
# SHORTAGE CALCULATOR
# =========================================================

@app.route("/api/shortage")
def shortage():

    roll_no = request.args.get(
        "roll_no"
    )

    target = float(
        request.args.get(
            "target",
            75
        )
    )

    student = df[
        df["Roll_No"] == str(roll_no)
    ]

    if student.empty:

        return jsonify({
            "error":
            "Student not found"
        }), 404

    present = int(
        (student["Status"] == "P").sum()
    )

    total = len(student)

    current = (
        present / total * 100
    )

    if current >= target:

        required = 0

    else:

        required = int(
            np.ceil(
                (
                    target * total
                    - 100 * present
                )
                /
                (100 - target)
            )
        )

    return jsonify({

        "roll_no": str(
            roll_no
        ),

        "current": round(
            current,
            2
        ),

        "target": target,

        "classes_attended": present,

        "classes_total": total,

        "classes_needed": required
    })


# =========================================================
# WHAT-IF CALCULATOR
# =========================================================

@app.route("/api/whatif")
def whatif():

    roll_no = request.args.get(
        "roll_no"
    )

    future_classes = int(
        request.args.get(
            "classes",
            10
        )
    )

    future_attended = int(
        request.args.get(
            "attend",
            10
        )
    )

    future_classes = max(
        0,
        future_classes
    )

    future_attended = max(
        0,
        min(
            future_attended,
            future_classes
        )
    )

    student = df[
        df["Roll_No"] == str(roll_no)
    ]

    if student.empty:

        return jsonify({
            "error":
            "Student not found"
        }), 404

    present = int(
        (student["Status"] == "P").sum()
    )

    total = len(student)

    current = (
        present / total * 100
    )

    projected = (
        (
            present
            + future_attended
        )
        /
        (
            total
            + future_classes
        )
        * 100
    )

    return jsonify({

        "current": round(
            current,
            2
        ),

        "future_classes":
            future_classes,

        "future_attend":
            future_attended,

        "projected": round(
            projected,
            2
        )
    })


# =========================================================
# RELOAD EXCEL + RETRAIN MODEL
# =========================================================

@app.route(
    "/api/reload",
    methods=["POST"]
)
def reload_data():

    global df
    global model

    df = load()

    model = train_model()

    return jsonify({

        "ok": True,

        "students": int(
            df["Roll_No"].nunique()
        ),

        "records": len(df)
    })


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )