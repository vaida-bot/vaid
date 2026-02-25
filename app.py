from flask import Flask, request, render_template_string
from groq import Groq
import os
import re

app = Flask(__name__)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VAID - AI Doctor</title>
<style>
body {
    margin: 0;
    font-family: 'Segoe UI', sans-serif;
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    color: white;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
}
.container {
    width: 95%;
    max-width: 500px;
    text-align: center;
}
h1 {
    font-size: 32px;
    margin-bottom: 20px;
}
button {
    width: 100%;
    padding: 15px;
    margin: 10px 0;
    font-size: 18px;
    border: none;
    border-radius: 10px;
    cursor: pointer;
}
.primary {
    background: #00c6ff;
    color: black;
}
.secondary {
    background: #ffffff22;
    color: white;
}
input, select {
    width: 100%;
    padding: 12px;
    margin: 8px 0;
    border-radius: 8px;
    border: none;
    font-size: 16px;
}
.result-box {
    margin-top: 20px;
    padding: 20px;
    border-radius: 12px;
    background: #ffffff11;
    font-size: 18px;
    text-align: left;
}
.risk-low { color: #00ff88; font-weight: bold; }
.risk-medium { color: #ffd000; font-weight: bold; }
.risk-high { color: #ff4c4c; font-weight: bold; }
</style>
</head>
<body>
<div class="container">
<h1>VAID AI Doctor</h1>

{% if not language %}
<form method="POST">
    <button name="language" value="english" class="primary">English</button>
    <button name="language" value="hindi" class="secondary">हिन्दी</button>
</form>

{% elif not result %}

<form method="POST">
<input type="hidden" name="language" value="{{language}}">

<select name="symptom" required>
<option value="">Select Primary Symptom</option>
<option>Cough</option>
<option>Fever</option>
<option>Headache</option>
<option>Chest Pain</option>
<option>Stomach Pain</option>
</select>

<input type="number" name="height" placeholder="Height (cm)" required>
<input type="number" name="weight" placeholder="Weight (kg)" required>

<button type="submit" class="primary">Analyze</button>
</form>

{% else %}

<div class="result-box">
<p><strong>Condition:</strong> {{condition}}</p>
<p><strong>Risk:</strong>
<span class="
{% if risk == 'Low' %}risk-low
{% elif risk == 'Medium' %}risk-medium
{% else %}risk-high
{% endif %}
">{{risk}}</span>
</p>
<p><strong>Action:</strong> {{action}}</p>
</div>

<form method="GET">
<button class="secondary">Start Over</button>
</form>

{% endif %}

</div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    language = None
    result = None
    condition = ""
    risk = ""
    action = ""

    if request.method == "POST":
        language = request.form.get("language")

        symptom = request.form.get("symptom")
        height = request.form.get("height")
        weight = request.form.get("weight")

        if symptom and height and weight:
            bmi = round(float(weight) / ((float(height)/100) ** 2), 1)

            prompt = f"""
You are a medical triage AI.

Symptom: {symptom}
BMI: {bmi}

Respond strictly in this format:

CONDITION: ...
RISK: Low / Medium / High
ACTION: ...
"""

            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": prompt}]
            )

            text = response.choices[0].message.content

            condition_match = re.search(r"CONDITION:\s*(.*)", text)
            risk_match = re.search(r"RISK:\s*(.*)", text)
            action_match = re.search(r"ACTION:\s*(.*)", text)

            condition = condition_match.group(1) if condition_match else "Unknown"
            risk = risk_match.group(1) if risk_match else "Medium"
            action = action_match.group(1) if action_match else "Consult doctor."

            result = True

    return render_template_string(
        HTML,
        language=language,
        result=result,
        condition=condition,
        risk=risk,
        action=action
    )

if __name__ == "__main__":
    app.run()