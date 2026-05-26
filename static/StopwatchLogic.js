let startBtn = document.getElementById('start');
let stopBtn = document.getElementById('stop');
let endSessionBtn = document.getElementById('end_session');
let returnBtn = document.getElementById('return');
let timer = false;
let hour = 0;
let minute = 0;
let second = 0;
let hrString = "00";
let minString = "00";
let secString = "00";
let totalSeconds = (hour * 3600) + (minute * 60) + second;
let name = "";
if (additional_stopwatch) {
    document.querySelector('[name="project_selector"]').addEventListener('change', function() {
        name = this.value;
        const h2 = document.createElement('h2');
        h2.textContent = name;
        h2.className = 'project_page_title';
        this.replaceWith(h2);
        document.getElementById("start").disabled=false
        document.getElementById("stop").disabled=false
        document.getElementById("end_session").disabled=false
        project_index = project_names.indexOf(name)
    });
}
startBtn.addEventListener('click', function () {
    timer = true;
    stopWatch();
});
stopBtn.addEventListener('click', function () {
    timer = false;
});
endSessionBtn.addEventListener('click', function() {
    timer = false;
    totalSeconds = (hour * 3600) + (minute * 60) + second;
    fetch('/save_session', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            seconds: totalSeconds,
            project_index: project_index,
            })
    }).then(response => response.json())
    .then(function(data) {
        alert(`Session complete!\nTime spent working this session: ${hrString}:${minString}:${secString}\nTotal time for this project: ${data.total_time}`);
        window.location.href = "/dashboard";
    });
});
returnBtn.addEventListener('click', function() {
    timer = false;
    window.location.href = "/dashboard_return";
});

function stopWatch() {
    if (timer) {
        second++;

        if (second == 60) {
            minute++;
            second = 0;
        }

        if (minute == 60) {
            hour++;
            minute = 0;
            second = 0;
        }

        hrString = hour;
        minString = minute;
        secString = second;

        if (hour < 10) {
            hrString = "0" + hrString;
        }

        if (minute < 10) {
            minString = "0" + minString;
        }

        if (second < 10) {
            secString = "0" + secString;
        }

        document.getElementById('hr').innerHTML = hrString;
        document.getElementById('min').innerHTML = minString;
        document.getElementById('sec').innerHTML = secString;
        setTimeout(stopWatch, 1000);
    }
}