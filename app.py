from flask import Flask, render_template_string, request
import os
from groq import Groq

app = Flask(__name__)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>VAID</title>
<style>
body {
    font-family: Arial, sans-serif;
    text-align: center;
    background: #f5f5f5;
    padding: 40px;
}
button {
    padding: 15px 25px;
    margin: 10px;
    font-size: 16px;
    border-radius: 8px;
    border: none;
    cursor: pointer;
}
.symptom { background: #ffffff; }
.submit { background: #222; color: white; }
</style>
</head>
<body>

<h2>VAID - AI Medical Triage</h2>

<form method="POST">
<h3>Select Symptoms</h3>

<button class="symptom" type="button" onclick="toggle(this)">Fever</button>
<button class="symptom" type="button" onclick="toggle(this)">Cough</button>
<button class="symptom" type="button" onclick="toggle(this)">Headache</button>
<button class="symptom" type="button" onclick="toggle(this)">Chest Pain</button>
<button class="symptom" type="button" onclick="toggle(this)">Breathing Issue</button>
<button class="symptom" type="button" onclick="toggle(this)">Fatigue</button>

<input type="hidden" name="symptoms" id="symptoms">

<h3>Optional Body Metrics</h3>
Height (cm): <input name="height"><br><br>
Weight (kg): <input name="weight"><br><br>

<button class="submit" type="submit">Analyze</button>
</form>

{% if result %}
<h3>AI Assessment</h3>
<p>{{ result }}</p>
{% endif %}

<script>
let selected = [];

function toggle(btn) {
    const text = btn.innerText;
    if (selected.includes(text)) {
        selected = selected.filter(x => x !== text);
        btn.style.background = "#ffffff";
    } else {
        selected.push(text);
        btn.style.background = "#add8e6";
    }
    document.getElementById("symptoms").value = selected.join(", ");
}
</script>

</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    if request.method == "POST":
        symptoms = request.form.get("symptoms")
        height = request.form.get("height")
        weight = request.form.get("weight")

        prompt = f"""
        Symptoms: {symptoms}
        Height: {height} cm
        Weight: {weight} kg

        Provide:
        1. Possible condition
        2. Risk level (Low/Medium/High)
        3. What to do next
        Keep it concise.
        """

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )

        result = response.choices[0].message.content

    return render_template_string(HTML, result=result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)