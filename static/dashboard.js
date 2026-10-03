let students = [];

let charts = {};


const $ = (id) =>
    document.getElementById(id);


async function getData(url) {

    const response =
        await fetch(url);

    const data =
        await response.json();

    if (!response.ok) {

        throw new Error(
            data.error ||
            "Request failed"
        );

    }

    return data;
}


// =====================================================
// PAGE NAVIGATION
// =====================================================

document
    .querySelectorAll(".nav")
    .forEach(button => {

        button.addEventListener(
            "click",
            () => {

                document
                    .querySelectorAll(".nav")
                    .forEach(x =>
                        x.classList.remove(
                            "active"
                        )
                    );

                document
                    .querySelectorAll(".page")
                    .forEach(x =>
                        x.classList.remove(
                            "active"
                        )
                    );

                button.classList.add(
                    "active"
                );

                const page =
                    button.dataset.page;

                $(page)
                    .classList.add(
                        "active"
                    );

                $("pageTitle")
                    .textContent =
                    button
                    .textContent
                    .replace(
                        /[^\w ]/g,
                        ""
                    )
                    .trim();

            }
        );

    });


// =====================================================
// LOAD DASHBOARD
// =====================================================

async function loadDashboard() {

    try {

        const summary =
            await getData(
                "/api/summary"
            );


        $("studentsCount")
            .textContent =
            summary.students;


        $("classesCount")
            .textContent =
            summary.classes;


        $("presentCount")
            .textContent =
            summary.present;


        $("absentCount")
            .textContent =
            summary.absent;


        $("attendanceCount")
            .textContent =
            summary.attendance + "%";


        students =
            await getData(
                "/api/students"
            );


        renderStudents(
            students
        );


        fillStudentSelectors();


        const daily =
            await getData(
                "/api/daily"
            );


        const monthly =
            await getData(
                "/api/monthly"
            );


        createChart(
            "dailyChart",
            "line",
            daily.map(
                x => x.date
            ),
            daily.map(
                x => x.attendance
            ),
            "Attendance %"
        );


        createChart(
            "monthlyChart",
            "bar",
            monthly.map(
                x => x.month
            ),
            monthly.map(
                x => x.attendance
            ),
            "Attendance %"
        );


        createChart(
            "studentChart",
            "bar",
            students.map(
                x => x.roll_no
            ),
            students.map(
                x => x.percentage
            ),
            "Attendance %"
        );


    }
    catch (error) {

        alert(
            error.message
        );

    }

}


// =====================================================
// STUDENT TABLE
// =====================================================

function renderStudents(
    list
) {

    $("studentTotal")
        .textContent =
        `${list.length} students`;


    $("studentTable")
        .innerHTML = "";


    list.forEach(
        student => {

            const row =
                document.createElement(
                    "tr"
                );


            let status =
                student.last_status === "P"
                    ? "Present"
                    : "Absent";


            let className =
                student.percentage >= 85
                    ? "good"
                    : student.percentage >= 75
                        ? "average"
                        : "risk";


            row.innerHTML = `

                <td>
                    <b>
                        ${student.roll_no}
                    </b>
                </td>

                <td>
                    ${student.classes}
                </td>

                <td>
                    ${student.present}
                </td>

                <td>
                    ${student.absent}
                </td>

                <td>
                    <span class="badge ${className}">
                        ${student.percentage}%
                    </span>
                </td>

                <td>
                    ${status}
                </td>

                <td>

                    <button
                        onclick="showStudent(
                            '${student.roll_no}'
                        )">

                        View

                    </button>

                </td>

            `;


            $("studentTable")
                .appendChild(row);

        }
    );

}


// =====================================================
// STUDENT SEARCH
// =====================================================

$("studentSearch")
    .addEventListener(
        "input",
        event => {

            const query =
                event.target.value
                .toLowerCase()
                .trim();


            const filtered =
                students.filter(
                    student =>
                        student.roll_no
                        .toLowerCase()
                        .includes(query)
                );


            renderStudents(
                filtered
            );

        }
    );


// =====================================================
// STUDENT SELECT BOXES
// =====================================================

function fillStudentSelectors() {

    const selectors = [

        "predStudent",

        "shortStudent",

        "whatStudent"

    ];


    selectors.forEach(
        id => {

            $(id).innerHTML = "";


            students.forEach(
                student => {

                    const option =
                        document.createElement(
                            "option"
                        );


                    option.value =
                        student.roll_no;


                    option.textContent =
                        student.roll_no;


                    $(id)
                        .appendChild(
                            option
                        );

                }
            );

        }
    );


    const date =
        new Date();


    date.setDate(
        date.getDate() + 1
    );


    $("predDate")
        .value =
        date.toISOString()
        .split("T")[0];

}


// =====================================================
// STUDENT DETAILS
// =====================================================

async function showStudent(
    rollNo
) {

    try {

        const student =
            await getData(
                "/api/student/" +
                encodeURIComponent(
                    rollNo
                )
            );


        $("studentDetail")
            .classList
            .remove(
                "hidden"
            );


        const history =
            student.history
            .slice(-20)
            .reverse();


        let historyHTML = "";


        history.forEach(
            item => {

                historyHTML += `

                    <div class="history-item">

                        <b>
                            ${item.date}
                        </b>

                        <span>
                            ${item.day}
                        </span>

                        <strong class="${
                            item.status === "P"
                                ? "present"
                                : "absent"
                        }">

                            ${
                                item.status === "P"
                                    ? "Present"
                                    : "Absent"
                            }

                        </strong>

                    </div>

                `;

            }
        );


        $("studentDetail")
            .innerHTML = `

                <div class="detail-header">

                    <div>

                        <h2>
                            Student:
                            ${student.roll_no}
                        </h2>

                        <p>
                            Complete attendance details
                        </p>

                    </div>

                </div>


                <div class="student-stats">

                    <div>
                        <b>
                            ${student.percentage}%
                        </b>
                        <span>
                            Attendance
                        </span>
                    </div>

                    <div>
                        <b>
                            ${student.present}
                        </b>
                        <span>
                            Present
                        </span>
                    </div>

                    <div>
                        <b>
                            ${student.absent}
                        </b>
                        <span>
                            Absent
                        </span>
                    </div>

                    <div>
                        <b>
                            ${student.classes}
                        </b>
                        <span>
                            Total Classes
                        </span>
                    </div>

                </div>


                <h3>
                    Recent Attendance
                </h3>

                <div class="history">

                    ${historyHTML}

                </div>

            `;


        $("studentDetail")
            .scrollIntoView({
                behavior: "smooth"
            });


    }
    catch (error) {

        alert(
            error.message
        );

    }

}


// =====================================================
// SINGLE DATE PREDICTION
// =====================================================

async function predict() {

    try {

        const rollNo =
            $("predStudent")
            .value;


        const date =
            $("predDate")
            .value;


        const result =
            await getData(
                `/api/predict?roll_no=${
                    encodeURIComponent(
                        rollNo
                    )
                }&date=${date}`
            );


        const status =
            result.status === "P"
                ? "PRESENT"
                : "ABSENT";


        $("predictionResult")
            .innerHTML = `

                <div class="prediction-box">

                    <h2>
                        ${result.date}
                    </h2>

                    <div class="prediction-status">

                        ${status}

                    </div>


                    <p>
                        Present Probability:
                        <b>
                            ${result.prob_present}%
                        </b>
                    </p>


                    <p>
                        Absent Probability:
                        <b>
                            ${result.prob_absent}%
                        </b>
                    </p>


                    <p>

                        ${
                            result.actual
                                ? "Actual Excel Record"
                                : "Machine Learning Prediction"
                        }

                    </p>

                </div>

            `;

    }
    catch (error) {

        $("predictionResult")
            .innerHTML = `
                <p class="error">
                    ${error.message}
                </p>
            `;

    }

}


// =====================================================
// FUTURE FORECAST
// =====================================================

async function forecast() {

    try {

        const rollNo =
            $("predStudent")
            .value;


        const days =
            $("forecastDays")
            .value;


        const results =
            await getData(
                `/api/future?roll_no=${
                    encodeURIComponent(
                        rollNo
                    )
                }&days=${days}`
            );


        let html = `

            <div class="table-wrapper">

                <table>

                    <thead>

                        <tr>

                            <th>
                                Date
                            </th>

                            <th>
                                Status
                            </th>

                            <th>
                                Present %
                            </th>

                            <th>
                                Absent %
                            </th>

                        </tr>

                    </thead>

                    <tbody>

        `;


        results.forEach(
            result => {

                html += `

                    <tr>

                        <td>
                            ${result.date}
                        </td>

                        <td>
                            ${
                                result.status === "P"
                                    ? "Present"
                                    : "Absent"
                            }
                        </td>

                        <td>
                            ${result.prob_present}%
                        </td>

                        <td>
                            ${result.prob_absent}%
                        </td>

                    </tr>

                `;

            }
        );


        html += `

                    </tbody>

                </table>

            </div>

        `;


        $("predictionResult")
            .innerHTML = html;

    }
    catch (error) {

        alert(
            error.message
        );

    }

}


// =====================================================
// SHORTAGE CALCULATOR
// =====================================================

async function shortage() {

    try {

        const rollNo =
            $("shortStudent")
            .value;


        const target =
            $("target")
            .value;


        const result =
            await getData(
                `/api/shortage?roll_no=${
                    encodeURIComponent(
                        rollNo
                    )
                }&target=${target}`
            );


        let message;


        if (
            result.classes_needed === 0
        ) {

            message =
                "Target attendance already reached.";

        }
        else {

            message =
                `You need to attend the next ${
                    result.classes_needed
                } classes continuously to reach ${
                    result.target
                }%.`;

        }


        $("shortResult")
            .innerHTML = `

                <div class="result-box">

                    <h3>
                        Current:
                        ${result.current}%
                    </h3>

                    <p>
                        Target:
                        ${result.target}%
                    </p>

                    <p>
                        ${message}
                    </p>

                </div>

            `;

    }
    catch (error) {

        alert(
            error.message
        );

    }

}


// =====================================================
// WHAT-IF CALCULATOR
// =====================================================

async function whatif() {

    try {

        const rollNo =
            $("whatStudent")
            .value;


        const classes =
            $("futureClasses")
            .value;


        const attend =
            $("futureAttend")
            .value;


        const result =
            await getData(
                `/api/whatif?roll_no=${
                    encodeURIComponent(
                        rollNo
                    )
                }&classes=${classes}&attend=${attend}`
            );


        $("whatResult")
            .innerHTML = `

                <div class="result-box">

                    <p>
                        Current Attendance:
                        <b>
                            ${result.current}%
                        </b>
                    </p>

                    <p>
                        Future Classes:
                        ${result.future_classes}
                    </p>

                    <p>
                        Future Classes Attended:
                        ${result.future_attend}
                    </p>

                    <h3>
                        Projected Attendance:
                        ${result.projected}%
                    </h3>

                </div>

            `;

    }
    catch (error) {

        alert(
            error.message
        );

    }

}


// =====================================================
// CHARTS
// =====================================================

function createChart(
    id,
    type,
    labels,
    data,
    label
) {

    if (charts[id]) {

        charts[id].destroy();

    }


    charts[id] =
        new Chart(
            $(id),
            {

                type: type,

                data: {

                    labels: labels,

                    datasets: [

                        {

                            label: label,

                            data: data,

                            borderWidth: 2,

                            tension: 0.3

                        }

                    ]

                },

                options: {

                    responsive: true,

                    maintainAspectRatio: true,

                    scales: {

                        y: {

                            beginAtZero: false

                        }

                    }

                }

            }
        );

}


// =====================================================
// RELOAD EXCEL
// =====================================================

async function reloadData() {

    try {

        await fetch(
            "/api/reload",
            {
                method: "POST"
            }
        );


        await loadDashboard();


        alert(
            "Excel data reloaded and ML model retrained."
        );

    }
    catch (error) {

        alert(
            error.message
        );

    }

}


// =====================================================
// START
// =====================================================

loadDashboard();